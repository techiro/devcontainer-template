import copy
import io
import json
from pathlib import Path
import tempfile
import urllib.error
import unittest
from unittest.mock import patch

import sdk_security_check as security


class SdkSecurityCheckTest(unittest.TestCase):
    def setUp(self):
        self.sleep_patch = patch.object(security.time, "sleep")
        self.sleep_patch.start()
        self.addCleanup(self.sleep_patch.stop)
        self.version = {"frameworkVersion": "3.47.8", "dartSdkVersion": "3.13.7"}
        self.advisories = [{
            "ghsa_id": security.KNOWN_ADVISORY,
            "severity": "high",
            "vulnerabilities": [{
                "package": {"name": "Dart SDK"},
                "vulnerable_version_range": "< 3.13.7 (stable), < 3.14.0-315.3.beta (beta)",
            }],
        }]

    def test_patched_stable_sdk_passes(self):
        self.assertEqual(len(security.check(self.version, self.advisories)), 1)

    def test_previous_published_sdk_is_rejected(self):
        with self.assertRaisesRegex(ValueError, security.KNOWN_ADVISORY):
            security.check({"frameworkVersion": "3.47.7", "dartSdkVersion": "3.13.5"}, self.advisories)

    def test_dart_downgrade_is_rejected_even_when_flutter_is_patched(self):
        self.version["dartSdkVersion"] = "3.13.6"
        with self.assertRaises(ValueError):
            security.check(self.version, self.advisories)

    def test_prerelease_is_not_mistaken_for_a_stable_fix(self):
        self.version["frameworkVersion"] = "3.50.0-0.2.pre"
        with self.assertRaises(ValueError):
            security.check(self.version, self.advisories)

    def test_new_high_advisory_blocks_previously_patched_sdk(self):
        new = copy.deepcopy(self.advisories[0])
        new["ghsa_id"] = "GHSA-test-new-advisory"
        new["vulnerabilities"][0]["vulnerable_version_range"] = ">= 3.13.0, < 3.13.8"
        with self.assertRaisesRegex(ValueError, "remains affected"):
            security.check(self.version, self.advisories + [new])

    def test_missing_known_advisory_does_not_silently_pass(self):
        with self.assertRaisesRegex(ValueError, "incomplete feed"):
            security.check(self.version, [])

    def test_unknown_high_package_requires_manual_review(self):
        self.advisories[0]["vulnerabilities"][0]["package"]["name"] = "Unknown SDK component"
        with self.assertRaisesRegex(ValueError, "unknown package"):
            security.check(self.version, self.advisories)

    def test_unknown_range_format_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "requires review"):
            security.affected((3, 13, 7), "prior to 3.13.8")

    def test_multiple_ranges_respect_boundaries(self):
        self.assertTrue(security.affected((3, 13, 6), ">= 3.13.0, < 3.13.7 || = 4.0.0"))
        self.assertFalse(security.affected((3, 13, 7), ">= 3.13.0, < 3.13.7 || = 4.0.0"))

    def test_advisory_network_failure_is_not_ignored(self):
        with patch.object(security.urllib.request, "urlopen", side_effect=OSError("offline")):
            with self.assertRaises(OSError):
                security.fetch_advisories()

    def test_transient_api_errors_retry_but_authentication_errors_do_not(self):
        request = security.urllib.request.Request("https://api.github.com/example")
        for code in (401, 403, 429, 500, 503):
            error = urllib.error.HTTPError(request.full_url, code, "error", {}, None)
            with self.subTest(code=code), patch.object(security.urllib.request, "urlopen", side_effect=error) as fetch:
                with self.assertRaises(urllib.error.HTTPError):
                    security.fetch_page(request)
                self.assertEqual(fetch.call_count, 1 if code in (401, 403) else 4)

    def test_transient_network_failure_can_recover(self):
        with patch.object(security.urllib.request, "urlopen", side_effect=[OSError("offline"), io.BytesIO(b"[]")]) as fetch:
            self.assertEqual(security.fetch_page(None), [])
            self.assertEqual(fetch.call_count, 2)

    def test_sdk_findings_and_partial_api_evidence_are_saved(self):
        with tempfile.TemporaryDirectory() as temp:
            versions, output = Path(temp) / "version.json", Path(temp) / "report.json"
            versions.write_text(json.dumps({"frameworkVersion": "3.47.7", "dartSdkVersion": "3.13.6"}))
            with patch.object(security, "fetch_page", side_effect=[self.advisories, []]):
                result = security.audit(versions, output)
            self.assertEqual(result["status"], "findings")
            self.assertEqual(result["blocking_count"], 2)
            self.assertEqual(len(json.loads(output.read_text())["pages"]), 2)
            auth_error = urllib.error.HTTPError("https://api.github.com", 401, "Unauthorized", {}, None)
            with patch.object(security, "fetch_page", side_effect=[self.advisories, auth_error]):
                result = security.audit(versions, output)
            self.assertEqual(result["status"], "error")
            self.assertIn("Authentication/permission failure: HTTP 401", result["reason"])
            self.assertEqual(len(result["pages"]), 1)

    def test_incomplete_feed_is_an_error_and_not_a_clean_audit(self):
        with tempfile.TemporaryDirectory() as temp:
            versions, output = Path(temp) / "version.json", Path(temp) / "report.json"
            versions.write_text(json.dumps(self.version))
            with patch.object(security, "fetch_page", return_value=[]):
                result = security.audit(versions, output)
            self.assertEqual(result["status"], "error")
            self.assertIn("incomplete feed", result["reason"])


if __name__ == "__main__":
    unittest.main()
