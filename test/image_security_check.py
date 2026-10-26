"""Gate fixable HIGH/CRITICAL OS findings; retain all findings in the input report."""
import collections
import json
import sys


def summarize(report, expected_image):
    metadata = report["Metadata"]
    if metadata["ImageID"] != expected_image:
        raise ValueError("Scanner image does not match the tested image")
    if metadata["OS"]["Family"] != "debian":
        raise ValueError("Expected a recognized Debian OS scan")
    results = [item for item in report["Results"] if item["Class"] == "os-pkgs"]
    if not results or not any(item.get("Packages") for item in results):
        raise ValueError("OS package inventory missing from image scan")
    vulnerabilities = [item for result in results for item in result.get("Vulnerabilities", [])]
    blocking = [item for item in vulnerabilities
                if item["Severity"] in ("HIGH", "CRITICAL") and item.get("FixedVersion")]
    return {
        "image": expected_image,
        "scope": "OS packages; SDK advisories and CLI npm audit are separate checks",
        "package_cve_counts": dict(collections.Counter(item["Severity"] for item in vulnerabilities)),
        "unique_cves": len({item["VulnerabilityID"] for item in vulnerabilities}),
        "fixable_high_critical": [{key: item[key] for key in
                                   ("VulnerabilityID", "PkgName", "InstalledVersion", "FixedVersion")}
                                  for item in blocking],
        "unfixed_high_critical_package_cve_count": sum(
            item["Severity"] in ("HIGH", "CRITICAL") and not item.get("FixedVersion")
            for item in vulnerabilities),
        "policy": "Block fixable HIGH/CRITICAL. Unfixed findings require release review; no zero-CVE claim.",
    }


if __name__ == "__main__":
    with open(sys.argv[1]) as source:
        report = json.load(source)
    with open(sys.argv[3]) as source:
        expected_image = source.read().strip()
    summary = summarize(report, expected_image)
    with open(sys.argv[2], "w") as destination:
        json.dump(summary, destination, indent=2)
    print(json.dumps(summary, indent=2))
    sys.exit(bool(summary["fixable_high_critical"]))
