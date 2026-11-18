import copy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import dependency_audit as audit


def npm_report(high=0):
    return {"auditReportVersion": 2, "vulnerabilities": {"example": {"severity": "high"}} if high else {},
            "metadata": {"vulnerabilities": {"info": 0, "low": 0, "moderate": 0,
                                             "high": high, "critical": 0, "total": high}}}


def os_report():
    return {"Metadata": {"ImageID": "sha256:test", "OS": {"Family": "debian"}},
            "Results": [{"Class": "os-pkgs", "Packages": [{"Name": "example"}], "Vulnerabilities": []}]}


class DependencyAuditTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.steps = {key: {"outcome": "success"} for key in
                      ("checkout", "setup_node", "install", "tests", "smoke", "npm", "sdk", "os")}
        self.addCleanup(patch.stopall)
        patch.object(audit, "tool_version", return_value="test-version").start()

    def write(self, name, value):
        audit.write_json(self.directory / name, value)

    def passing_reports(self):
        for kind in audit.AUDITS:
            self.write(f"{kind}-result.json", {"status": "pass", "reason": "", "blocking_count": 0, "review_count": 0})
            for name in audit.EVIDENCE[kind]:
                self.write(name, {})
        self.write("os-vulnerabilities.json", os_report())
        (self.directory / "image-id.txt").write_text("sha256:test")

    def test_npm_high_is_a_finding_and_api_errors_are_not_findings(self):
        self.assertEqual(audit.npm_result(npm_report(1), 1)["status"], "findings")
        for report, code in (({"error": {"code": "E403"}}, 1), (npm_report(), 1), (npm_report(), 2), ({}, 0)):
            with self.subTest(report=report, code=code), self.assertRaises((ValueError, KeyError)):
                audit.npm_result(report, code)

    def test_missing_prerequisites_are_recorded_for_every_audit(self):
        for kind in audit.AUDITS:
            result = audit.run_audit(kind, self.directory)
            self.assertEqual(result["status"], "skipped")
            self.assertIn("Prerequisite unavailable", result["reason"])
            self.assertTrue((self.directory / f"{kind}-result.json").exists())

    def test_malformed_npm_response_is_saved_and_fails_closed(self):
        self.write("cli-package-lock.json", {})
        def capture(*args, **kwargs):
            (self.directory / "cli-audit.json").write_text("not json")
            return 0
        with patch.object(audit, "capture", side_effect=capture):
            result = audit.run_audit("npm", self.directory, "cli")
        self.assertEqual(result["status"], "error")
        self.assertEqual((self.directory / "cli-audit.json").read_text(), "not json")

    def test_npm_failure_does_not_prevent_sdk_or_os_audits(self):
        self.write("cli-package-lock.json", {})
        self.write("sdk-version.json", {})
        (self.directory / "image-id.txt").write_text("sha256:test")
        (self.directory / "image-ref.txt").write_text("tested-image")
        def capture(command, directory, name, **kwargs):
            if name == "cli-audit":
                self.write(name + ".json", npm_report(1))
                return 1
            self.write(name + ".json", os_report() if name == "os-vulnerabilities" else {"bomFormat": "CycloneDX"})
            return 0
        with patch.object(audit, "capture", side_effect=capture), \
                patch.object(audit, "audit_sdk", return_value={"status": "pass", "reason": "", "blocking_count": 0, "evaluated": []}), \
                patch.object(audit.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, stdout="Trivy test")), \
                patch.dict(os.environ, {"TRIVY_IMAGE": "scanner@sha256:test"}):
            self.assertEqual(audit.run_audit("npm", self.directory, "cli")["status"], "findings")
            self.assertEqual(audit.run_audit("sdk", self.directory)["status"], "pass")
            self.assertEqual(audit.run_audit("os", self.directory)["status"], "pass")

    def test_aggregate_passes_only_with_all_checks_and_evidence(self):
        self.passing_reports()
        self.assertTrue(audit.aggregate(self.directory, self.steps)["passed"])
        for step in self.steps:
            steps = copy.deepcopy(self.steps)
            steps[step]["outcome"] = "failure"
            with self.subTest(step=step):
                self.assertFalse(audit.aggregate(self.directory, steps)["passed"])

    def test_missing_or_invalid_evidence_blocks_release(self):
        for name in ("sdk-result.json", "cli-package-lock.json", "os-sbom.cdx.json"):
            self.passing_reports()
            (self.directory / name).unlink()
            with self.subTest(missing=name):
                self.assertFalse(audit.aggregate(self.directory, self.steps)["passed"])
        self.passing_reports()
        (self.directory / "npm-result.json").write_text("[]")
        self.assertFalse(audit.aggregate(self.directory, self.steps)["passed"])

    def test_wrong_image_is_rejected_by_final_gate(self):
        self.passing_reports()
        (self.directory / "image-id.txt").write_text("sha256:wrong")
        self.assertFalse(audit.aggregate(self.directory, self.steps)["passed"])

    def test_unfixed_findings_are_visible_without_blocking(self):
        self.passing_reports()
        self.write("os-result.json", {"status": "pass", "reason": "", "blocking_count": 0, "review_count": 3})
        result = audit.aggregate(self.directory, self.steps)
        self.assertTrue(result["passed"])
        self.assertIn("未修正のOS High/Critical", audit.markdown(result))

    def test_missing_results_still_produce_a_summary_and_nonzero_exit(self):
        env = dict(os.environ, AUDIT_STEPS=json.dumps(self.steps), GITHUB_STEP_SUMMARY=str(self.directory / "summary.md"))
        result = subprocess.run(["python3", str(Path(audit.__file__)), "summary", "--reports", str(self.directory)],
                                env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertFalse(audit.read_json(self.directory / "audit-summary.json")["passed"])
        self.assertIn("公開を停止", (self.directory / "summary.md").read_text())

    def test_smoke_failure_keeps_image_and_sdk_evidence_for_audits(self):
        # Exercise the real shell script with fake container commands, failing after version capture.
        bin_dir = self.directory / "bin"
        bin_dir.mkdir()
        commands = {
            "docker": '#!/bin/bash\ncase "$1" in\n ps) echo container123;;\n inspect) echo tested-image;;\n image) if [ "$2" = inspect ]; then echo sha256:test; fi;;\nesac\n',
            "devcontainer": '#!/bin/bash\nif [ "$1" = exec ]; then\n if [ "$4" = flutter ]; then echo \'{"frameworkVersion":"3.47.9","dartSdkVersion":"3.13.7"}\'; else exit 17; fi\nfi\n',
        }
        for name, contents in commands.items():
            target = bin_dir / name
            target.write_text(contents)
            target.chmod(0o755)
        env = dict(os.environ, PATH=str(bin_dir) + os.pathsep + os.environ["PATH"],
                   XDG_CACHE_HOME=str(self.directory / "cache"), SECURITY_REPORT_DIR=str(self.directory))
        result = subprocess.run(["bash", str(Path(audit.__file__).with_name("flutter-smoke.sh"))], env=env,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 17, result.stderr)
        self.assertEqual((self.directory / "image-id.txt").read_text().strip(), "sha256:test")
        self.assertEqual(audit.read_json(self.directory / "sdk-version.json")["frameworkVersion"], "3.47.9")
        # Both prerequisites survive cleanup, so an independent later audit can use them.
        self.assertTrue((self.directory / "image-ref.txt").exists())


if __name__ == "__main__":
    unittest.main()
