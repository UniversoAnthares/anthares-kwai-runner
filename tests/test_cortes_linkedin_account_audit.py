"""Pure tests for the read-only LinkedIn identity audit."""
import unittest
from tools.cortes_linkedin_account_audit import classify, COMPANY_ID

class AccountAuditTests(unittest.TestCase):
    def test_company_and_personal_are_separate(self):
        observed = classify([
            {"service":"linkedin","id":COMPANY_ID,
             "externalLink":"https://www.linkedin.com/company/145345334/"},
            {"service":"linkedin","id":"other-member",
             "externalLink":"https://www.linkedin.com/in/member-example/"},
        ])
        self.assertEqual(observed, {
            "company_verified":True,
            "personal_profiles_connected":1,
            "ambiguous_linkedin_channels":0,
        })

    def test_personal_ownership_not_inferred_from_admin_company(self):
        observed = classify([
            {"service":"linkedin","id":COMPANY_ID,
             "externalLink":"https://www.linkedin.com/company/145345334/"},
        ])
        self.assertTrue(observed["company_verified"])
        self.assertEqual(observed["personal_profiles_connected"],0)

    def test_unknown_linked_profile_remains_ambiguous(self):
        observed = classify([{"service":"linkedin","id":"unknown","externalLink":""}])
        self.assertEqual(observed["ambiguous_linkedin_channels"],1)
        self.assertFalse(observed["company_verified"])

if __name__ == "__main__":
    unittest.main()
