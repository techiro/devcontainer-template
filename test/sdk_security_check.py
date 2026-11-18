"""Fail closed on unsupported/high SDK advisories; only final stable SDKs are supported."""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

KNOWN_ADVISORY = "GHSA-frr6-h895-5pxp"
MINIMUM = {"Flutter SDK": (3, 47, 8), "Dart SDK": (3, 13, 7)}


def stable_version(value):
    if not re.fullmatch(r"\d+\.\d+\.\d+", value):
        raise ValueError(f"Expected a final stable SDK version, got {value!r}")
    return tuple(map(int, value.split(".")))


def affected(version, expression):
    if "(stable)" in expression:
        expression = expression.split("(stable)", 1)[0].strip()
    alternatives = expression.split("||")
    for alternative in alternatives:
        terms = re.findall(r"(<=|>=|<|>|=)?\s*(\d+\.\d+\.\d+)", alternative)
        remainder = re.sub(r"(<=|>=|<|>|=)?\s*\d+\.\d+\.\d+", "", alternative)
        if not terms or re.sub(r"[\s,&]", "", remainder):
            raise ValueError(f"Advisory range requires review: {expression!r}")
        matches = []
        for operator, value in terms:
            target = stable_version(value)
            matches.append({"<": version < target, "<=": version <= target,
                            ">": version > target, ">=": version >= target,
                            "=": version == target, "": version == target}[operator])
        if all(matches):
            return True
    return False


class VulnerabilityError(ValueError):
    """A supported advisory or minimum-version rule found a vulnerable SDK."""


def check(version_info, advisories, evaluated=None):
    versions = {"Flutter SDK": stable_version(version_info["frameworkVersion"]),
                "Dart SDK": stable_version(version_info["dartSdkVersion"].split()[0])}
    if KNOWN_ADVISORY not in {a["ghsa_id"] for a in advisories}:
        raise ValueError("Required upstream advisory missing; refusing an incomplete feed")
    if evaluated is None:
        evaluated = []
    for advisory in advisories:
        if advisory["severity"] not in ("high", "critical"):
            continue
        if not advisory.get("vulnerabilities"):
            raise ValueError(f"{advisory['ghsa_id']}: missing vulnerability data")
        for vulnerability in advisory["vulnerabilities"]:
            package = vulnerability["package"]["name"]
            if package not in versions:
                raise ValueError(f"{advisory['ghsa_id']}: unknown package {package!r}; review required")
            evaluated.append({"advisory": advisory["ghsa_id"], "package": package,
                              "version": list(versions[package]),
                              "affected": affected(versions[package], vulnerability["vulnerable_version_range"])})
    for package, minimum in MINIMUM.items():
        if versions[package] < minimum and not any(
                item["advisory"] == KNOWN_ADVISORY and item["package"] == package and item["affected"]
                for item in evaluated):
            evaluated.append({"advisory": KNOWN_ADVISORY, "package": package,
                              "version": list(versions[package]), "affected": True})
    findings = [item for item in evaluated if item["affected"]]
    if findings:
        raise VulnerabilityError("; ".join(
            f"{item['advisory']}: {item['package']} remains affected" for item in findings))
    return evaluated


def fetch_page(request):
    # Three retries after the initial request, bounded even when Retry-After is large.
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code != 429 and not 500 <= error.code <= 599:
                raise
            if attempt == 3:
                raise
        except OSError:
            if attempt == 3:
                raise
        time.sleep(2 ** attempt)


def fetch_advisories(evidence=None):
    advisories = {}
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "flutter-template-security-check",
               "X-GitHub-Api-Version": "2022-11-28"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    for repository in ("dart-lang/sdk", "flutter/flutter"):
        page = 1
        while True:
            url = f"https://api.github.com/repos/{repository}/security-advisories?per_page=100&page={page}"
            data = fetch_page(urllib.request.Request(url, headers=headers))
            if evidence is not None:
                evidence.append({"repository": repository, "page": page, "response": data})
            if not isinstance(data, list):
                raise ValueError("Unexpected advisory response")
            for advisory in data:
                advisories[advisory["ghsa_id"]] = advisory
            if len(data) < 100:
                break
            page += 1
    return list(advisories.values())


def audit(version_path, output_path):
    from pathlib import Path
    result = {"status": "error", "reason": "", "versions": None,
              "pages": [], "evaluated": [], "blocking_count": 0}
    try:
        result["versions"] = json.loads(Path(version_path).read_text())
        advisories = fetch_advisories(result["pages"])
        check(result["versions"], advisories, result["evaluated"])
        result["status"] = "pass"
    except VulnerabilityError as error:
        result.update(status="findings", reason=str(error))
    except urllib.error.HTTPError as error:
        category = "Authentication/permission failure" if error.code in (401, 403) else "Advisory API failure"
        result["reason"] = f"{category}: HTTP {error.code}"
    except Exception as error:
        result["reason"] = f"{type(error).__name__}: {error}"
    result["blocking_count"] = sum(item["affected"] for item in result["evaluated"])
    Path(output_path).write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    result = audit(sys.argv[1], sys.argv[2])
    print(result["reason"] or "Upstream stable SDK advisory checks passed")
    sys.exit(result["status"] != "pass")
