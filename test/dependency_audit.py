"""Run independent dependency audits and assemble a fail-closed CI report."""
import argparse
from datetime import datetime, timezone
import html
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

from image_security_check import summarize as summarize_image
from sdk_security_check import audit as audit_sdk

AUDITS = ("npm", "sdk", "os")
STATES = {"pass", "findings", "error", "skipped"}
EVIDENCE = {
    "npm": ("cli-audit.json", "cli-package-lock.json"),
    "sdk": ("sdk-version.json", "sdk-advisories.json"),
    "os": ("os-vulnerabilities.json", "os-sbom.cdx.json", "security-summary.json"),
}


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def read_json(path):
    return json.loads(path.read_text())


def capture(command, directory, name, timeout=120):
    with (directory / f"{name}.json").open("w") as stdout, (directory / f"{name}.stderr.txt").open("w") as stderr:
        return subprocess.run(command, stdout=stdout, stderr=stderr, timeout=timeout).returncode


def npm_result(report, returncode):
    if report.get("error") or report.get("auditReportVersion") != 2:
        raise ValueError("npm returned an API error or unsupported audit report; see cli-audit.json")
    if not isinstance(report["vulnerabilities"], dict):
        raise ValueError("npm vulnerability inventory is invalid")
    counts = report["metadata"]["vulnerabilities"]
    if any(type(counts.get(key)) is not int or counts[key] < 0
           for key in ("info", "low", "moderate", "high", "critical", "total")):
        raise ValueError("npm vulnerability counts are missing or invalid")
    if counts["total"] != sum(counts[key] for key in ("info", "low", "moderate", "high", "critical")):
        raise ValueError("npm vulnerability totals are inconsistent")
    blocking = counts["high"] + counts["critical"]
    if returncode not in (0, 1) or (returncode == 1 and not blocking):
        raise ValueError(f"npm audit failed without a supported blocking finding (exit {returncode})")
    return {"status": "findings" if blocking else "pass", "blocking_count": blocking,
            "counts": counts, "reason": "Update CLI dependencies with High/Critical findings" if blocking else ""}


def run_audit(kind, directory, cli_prefix=None):
    directory.mkdir(parents=True, exist_ok=True)
    result = {"status": "error", "reason": "", "blocking_count": 0, "review_count": 0}
    try:
        prerequisites = {"npm": ("cli-package-lock.json",), "sdk": ("sdk-version.json",),
                         "os": ("image-id.txt", "image-ref.txt")}[kind]
        missing = [name for name in prerequisites if not (directory / name).is_file()]
        if missing:
            result.update(status="skipped", reason="Prerequisite unavailable: " + ", ".join(missing))
        elif kind == "npm":
            if not cli_prefix:
                raise ValueError("CLI install prefix is required")
            code = capture(["npm", "audit", "--prefix", cli_prefix, "--audit-level=high", "--json"],
                           directory, "cli-audit")
            result.update(npm_result(read_json(directory / "cli-audit.json"), code))
        elif kind == "sdk":
            report = audit_sdk(directory / "sdk-version.json", directory / "sdk-advisories.json")
            result.update({key: report[key] for key in ("status", "reason", "blocking_count")})
            result["counts"] = {"evaluated_package_advisories": len(report["evaluated"])}
        else:
            image_ref = (directory / "image-ref.txt").read_text().strip()
            expected_image = (directory / "image-id.txt").read_text().strip()
            if not image_ref or not expected_image:
                raise ValueError("Tested image identity is empty")
            scanner = os.environ["TRIVY_IMAGE"]
            base = ["docker", "run", "--rm", "-v", f"{directory.resolve()}:/reports"]
            version = subprocess.run(["docker", "run", "--rm", scanner, "--version"],
                                     capture_output=True, text=True, timeout=120, check=True)
            (directory / "trivy-version.txt").write_text(version.stdout)
            code = capture(base + ["-v", "/var/run/docker.sock:/var/run/docker.sock:ro", scanner,
                           "image", "--scanners", "vuln", "--pkg-types", "os", "--no-progress",
                           "--timeout", "15m", "--format", "json", image_ref],
                           directory, "os-vulnerabilities", timeout=1000)
            if code:
                raise ValueError(f"Trivy scan failed (exit {code}); see os-vulnerabilities.stderr.txt")
            details = summarize_image(read_json(directory / "os-vulnerabilities.json"), expected_image)
            write_json(directory / "security-summary.json", details)
            result.update(blocking_count=len(details["fixable_high_critical"]),
                          review_count=details["unfixed_high_critical_package_cve_count"],
                          counts=details["package_cve_counts"])
            code = capture(base + [scanner, "convert", "--format", "cyclonedx",
                                   "/reports/os-vulnerabilities.json"], directory, "os-sbom.cdx")
            if code or read_json(directory / "os-sbom.cdx.json").get("bomFormat") != "CycloneDX":
                raise ValueError("OS SBOM conversion failed or returned an invalid report")
            result.update(status="findings" if result["blocking_count"] else "pass",
                          reason="Upgrade OS packages with fixable High/Critical findings"
                          if result["blocking_count"] else "")
    except Exception as error:
        result.update(status="error", reason=f"{type(error).__name__}: {error}")
    write_json(directory / f"{kind}-result.json", result)
    return result


def tool_version(command):
    try:
        return subprocess.run(command, capture_output=True, text=True, check=True, timeout=15).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "unavailable"


def aggregate(directory, steps):
    audits = {}
    for kind in AUDITS:
        try:
            result = read_json(directory / f"{kind}-result.json")
            if result["status"] not in STATES or not isinstance(result["reason"], str):
                raise ValueError("Invalid audit status/reason")
            for key in ("blocking_count", "review_count"):
                if type(result[key]) is not int or result[key] < 0:
                    raise ValueError(f"Invalid {key}")
            if result["status"] == "pass":
                if result["blocking_count"] or steps.get(kind, {}).get("outcome") != "success":
                    raise ValueError("Pass result contradicts findings or step outcome")
                for name in EVIDENCE[kind]:
                    read_json(directory / name)
                if kind == "os":
                    # Revalidate image identity at the final gate, too.
                    summarize_image(read_json(directory / "os-vulnerabilities.json"),
                                    (directory / "image-id.txt").read_text().strip())
        except Exception as error:
            result = {"status": "error", "reason": f"Missing/invalid result: {error}",
                      "blocking_count": 0, "review_count": 0}
        audits[kind] = result
    required = {name: steps.get(name, {}).get("outcome", "missing")
                for name in ("checkout", "setup_node", "install", "tests", "smoke")}
    passed = all(value == "success" for value in required.values()) and all(
        result["status"] == "pass" for result in audits.values())
    sdk_path = directory / "sdk-version.json"
    try:
        sdk_version = read_json(sdk_path)
    except (OSError, ValueError):
        sdk_version = None
    return {"schema_version": 1, "passed": passed, "audits": audits, "steps": required,
            "provenance": {
                "commit": os.environ.get("GITHUB_SHA", "unknown"),
                "run_url": f"{os.environ.get('GITHUB_SERVER_URL', 'https://github.com')}/"
                           f"{os.environ.get('GITHUB_REPOSITORY', '')}/actions/runs/{os.environ.get('GITHUB_RUN_ID', '')}",
                "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT", "unknown"),
                "recorded_at": datetime.now(timezone.utc).isoformat(),
                "architecture": platform.machine(), "sdk": sdk_version,
                "image_id": (directory / "image-id.txt").read_text().strip()
                if (directory / "image-id.txt").exists() else None,
                "tools": {"python": platform.python_version(), "node": tool_version(["node", "--version"]),
                          "npm": tool_version(["npm", "--version"]),
                          "docker": tool_version(["docker", "--version"]),
                          "devcontainer": tool_version(["devcontainer", "--version"]),
                          "trivy_image": os.environ.get("TRIVY_IMAGE", "unknown"),
                          "trivy": (directory / "trivy-version.txt").read_text().strip()
                          if (directory / "trivy-version.txt").exists() else "unavailable"}}}


def markdown(report):
    def cell(value):
        return html.escape(str(value)).replace("|", "&#124;").replace("\n", " ").replace("\r", " ")
    labels = {"pass": "合格", "findings": "脆弱性あり", "error": "実行エラー", "skipped": "未実施"}
    lines = ["## Dependency audit", "", f"Architecture: {cell(report['provenance']['architecture'])}", "",
             "判定: " + ("合格" if report["passed"] else "公開を停止"), "",
             "| 対象 | 状態 | 件数内訳 | 停止対象件数 | 要確認件数 | 理由・対応 |",
             "|---|---|---|---:|---:|---|"]
    for kind, result in report["audits"].items():
        reason = result["reason"]
        if result["review_count"]:
            reason += " 未修正のOS High/Criticalあり。公開前に要確認。"
        counts = ", ".join(f"{key}: {value}" for key, value in result.get("counts", {}).items())
        lines.append(f"| {kind} | {labels[result['status']]} | {cell(counts)} | {result['blocking_count']} | "
                     f"{result['review_count']} | {cell(reason)} |")
    lines += ["", "件数はnpmではパッケージ数、SDKではパッケージ×アドバイザリ数、OSではパッケージ×CVE数です。",
              "", "### Build and validation", ""]
    lines += [f"- {name}: {cell(outcome)}" for name, outcome in report["steps"].items()]
    lines += ["", "詳細・証拠・バージョン情報は、この実行の security-* Artifact を参照してください。", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=(*AUDITS, "summary"))
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--cli-prefix")
    args = parser.parse_args()
    args.reports.mkdir(parents=True, exist_ok=True)
    if args.command != "summary":
        result = run_audit(args.command, args.reports, args.cli_prefix)
        print(json.dumps(result, indent=2))
        return int(result["status"] != "pass")
    report = aggregate(args.reports, json.loads(os.environ.get("AUDIT_STEPS", "{}")))
    write_json(args.reports / "audit-summary.json", report)
    rendered = markdown(report)
    (args.reports / "audit-summary.md").write_text(rendered)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as summary:
            summary.write(rendered)
    print(rendered)
    return int(not report["passed"])


if __name__ == "__main__":
    sys.exit(main())
