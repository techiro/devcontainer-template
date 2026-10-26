import unittest

from image_security_check import summarize


class ImageSecurityCheckTest(unittest.TestCase):
    def setUp(self):
        self.report = {"Metadata": {"ImageID": "sha256:test", "OS": {"Family": "debian"}},
                       "Results": [{"Class": "os-pkgs", "Packages": [{"Name": "example"}],
                                    "Vulnerabilities": []}]}

    def add_finding(self, severity, fixed):
        self.report["Results"][0]["Vulnerabilities"].append({
            "Severity": severity, "FixedVersion": fixed, "InstalledVersion": "1",
            "VulnerabilityID": "CVE-test", "PkgName": "example"})

    def test_fixable_high_is_blocking(self):
        self.add_finding("HIGH", "2")
        self.assertEqual(len(summarize(self.report, "sha256:test")["fixable_high_critical"]), 1)

    def test_unfixed_critical_is_explicitly_reported(self):
        self.add_finding("CRITICAL", "")
        result = summarize(self.report, "sha256:test")
        self.assertEqual(result["unfixed_high_critical_package_cve_count"], 1)
        self.assertEqual(result["fixable_high_critical"], [])

    def test_medium_is_visible_without_blocking(self):
        self.add_finding("MEDIUM", "2")
        result = summarize(self.report, "sha256:test")
        self.assertEqual(result["package_cve_counts"], {"MEDIUM": 1})
        self.assertEqual(result["fixable_high_critical"], [])

    def test_wrong_image_cannot_pass(self):
        with self.assertRaises(ValueError):
            summarize(self.report, "sha256:other")

    def test_missing_inventory_cannot_pass_as_clean(self):
        self.report["Results"] = []
        with self.assertRaises(ValueError):
            summarize(self.report, "sha256:test")


if __name__ == "__main__":
    unittest.main()
