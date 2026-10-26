import copy
import unittest
from unittest.mock import patch

import sdk_security_check as security


class SdkSecurityCheckTest(unittest.TestCase):
    def setUp(self):
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


if __name__ == "__main__":
    unittest.main()
