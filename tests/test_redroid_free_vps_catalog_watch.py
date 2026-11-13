import unittest
from unittest.mock import patch
from tools import redroid_free_vps_catalog_watch as mod


class CatalogWatchTests(unittest.TestCase):
    def test_vpsfree_catalog_overrides_marketing(self):
        fake = "Default Free Tier 2 vCPU / 4GB RAM; plans: 192MB NAT VPS $0.00 /10 days"
        self.assertEqual(mod.evaluate("vpsfree", 200, fake),
                         "FREE_LISTING_BELOW_REDROID_MINIMUM")

    def test_verta_advertised_is_not_provisioned(self):
        self.assertEqual(mod.evaluate("verta", 200, "Linux VPS Free! 2 vCPU 4GB RAM"),
                         "FOUR_GB_ADVERTISED_NO_DELIVERY_PROOF")

    def test_nanokvm_low_memory_and_core(self):
        self.assertEqual(mod.evaluate("nanokvm", 200, "1 Core 2048MB Low Stock"),
                         "ONE_CORE_TWO_GB_NOT_QUALIFIED")

    def test_cloudflare_error_not_promoted(self):
        self.assertEqual(mod.evaluate("nevatal", 530, "Cloudflare tunnel 1033"),
                         "ORIGIN_UNAVAILABLE")

    def test_android_offer_is_not_server_evidence(self):
        self.assertEqual(mod.evaluate("nevatal", 200, "FREE Android Cloud"),
                         "ANDROID_OFFER_UNVERIFIED_NO_HOST")

    def test_markup_script_does_not_forge_status(self):
        html = "<script>192MB NAT VPS $0.00</script><main>Free VPS unknown</main>"
        self.assertEqual(mod.evaluate("vpsfree", 200, mod.normalized_markup(html)),
                         "FREE_CATALOG_UNVERIFIED")

    def test_no_secret_login_or_vm_automatically(self):
        with patch.object(mod, "fetch_public",
                          return_value={"provider":"test","status":"FETCH_UNAVAILABLE"}):
            data=mod.report()
        self.assertFalse(data["secrets_used"])
        self.assertFalse(data["any_vm_allocated"])
        self.assertFalse(data["any_provider_approved"])
        self.assertEqual(len(data["results"]),4)

    def test_non_200_always_unavailable(self):
        self.assertEqual(mod.evaluate("verta", 429, "4GB RAM free"),"ORIGIN_UNAVAILABLE")
        self.assertEqual(mod.evaluate("verta", 403, "4GB RAM free"),"HTTP_ERROR")


if __name__ == "__main__":
    unittest.main()
