"""Fail closed on unsupported/high SDK advisories; only final stable SDKs are supported."""
import json
import os
import re
import sys
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


def check(version_info, advisories):
    versions = {"Flutter SDK": stable_version(version_info["frameworkVersion"]),
                "Dart SDK": stable_version(version_info["dartSdkVersion"].split()[0])}
    for package, minimum in MINIMUM.items():
        if versions[package] < minimum:
            raise ValueError(f"{KNOWN_ADVISORY}: {package} {versions[package]} < {minimum}")
    if KNOWN_ADVISORY not in {a["ghsa_id"] for a in advisories}:
        raise ValueError("Required upstream advisory missing; refusing an incomplete feed")
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
            if affected(versions[package], vulnerability["vulnerable_version_range"]):
                raise ValueError(f"{advisory['ghsa_id']}: {package} remains affected")
            evaluated.append({"advisory": advisory["ghsa_id"], "package": package,
                              "version": list(versions[package]), "affected": False})
    return evaluated


def fetch_advisories():
    advisories = {}
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "flutter-template-security-check",
               "X-GitHub-Api-Version": "2022-11-28"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    for repository in ("dart-lang/sdk", "flutter/flutter"):
        page = 1
        while True:
            url = f"https://api.github.com/repos/{repository}/security-advisories?per_page=100&page={page}"
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as response:
                data = json.load(response)
            if not isinstance(data, list):
                raise ValueError("Unexpected advisory response")
            for advisory in data:
                advisories[advisory["ghsa_id"]] = advisory
            if len(data) < 100:
                break
            page += 1
    return list(advisories.values())


if __name__ == "__main__":
    with open(sys.argv[1]) as source:
        version_info = json.load(source)
    result = {"versions": version_info, "evaluated": check(version_info, fetch_advisories())}
    with open(sys.argv[2], "w") as destination:
        json.dump(result, destination, indent=2)
    print("Upstream stable SDK advisory checks passed")
