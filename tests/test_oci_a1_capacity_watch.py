"""No-credential regression checks for the GitHub-hosted OCI A1 watcher."""
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from tools import oci_a1_capacity_watch as mod


class SafeDefaults(unittest.TestCase):
    def test_no_secret_means_no_oracle_client(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(mod.auth())
            self.assertEqual(mod.main(), 0)

    def test_pages_are_exhaustive(self):
        calls = []
        def call(page=None):
            calls.append(page)
            if page is None:
                return SimpleNamespace(data=[1], headers={"opc-next-page": "next"})
            self.assertEqual(page, "next")
            return SimpleNamespace(data=[2], headers={})
        self.assertEqual(mod.pages(call), [1, 2])
        self.assertEqual(calls, [None, "next"])

    def test_wrong_region_is_rejected_before_oci_api(self):
        with patch.dict(os.environ, {"OCI_A1_WATCH_AUTH_JSON":
                '{"user":"u","tenancy":"t","fingerprint":"f","region":"us-ashburn-1",'
                '"private_key":"-----BEGIN PRIVATE KEY-----example"}'}, clear=True):
            with self.assertRaises(ValueError):
                mod.auth()

    def test_sdk_client_config_has_required_fields_with_signer(self):
        sample = '{"user":"oci_user","tenancy":"oci_tenancy",' \
                 '"fingerprint":"oci_fp","region":"sa-saopaulo-1",' \
                 '"private_key":"-----BEGIN PRIVATE KEY-----example"}'
        configs = []

        def inspect_client(config, **kwargs):
            configs.append(config)
            self.assertIsNotNone(kwargs.get("signer"))
            self.assertTrue(all(k in config for k in (
                "region", "tenancy", "user", "fingerprint", "key_file")))
            return object()

        with patch.dict(os.environ, {"OCI_A1_WATCH_AUTH_JSON": sample},
                        clear=True), \
             patch.object(mod.oci.signer, "Signer", return_value=object()), \
             patch.object(mod.oci.core, "ComputeClient",
                          side_effect=inspect_client), \
             patch.object(mod.oci.core, "VirtualNetworkClient",
                          side_effect=inspect_client), \
             patch.object(mod.oci.core, "BlockstorageClient",
                          side_effect=inspect_client), \
             patch.object(mod.oci.identity, "IdentityClient",
                          side_effect=inspect_client):
            self.assertEqual(len(mod.auth()), 5)
        self.assertEqual(len(configs), 4)

    def test_public_subnet_without_nat_cannot_provision(self):
        subnet = SimpleNamespace(
            prohibit_public_ip_on_vnic=False, route_table_id="route",
            vcn_id="vcn")
        network = SimpleNamespace(get_route_table=lambda _: None)
        self.assertFalse(mod.private_network_egress_ready(network, subnet))

    def test_igw_route_rejects_private_ip_vm(self):
        subnet = SimpleNamespace(
            prohibit_public_ip_on_vnic=True, route_table_id="route",
            vcn_id="vcn")
        rule = SimpleNamespace(destination="0.0.0.0/0",
                               destination_type="CIDR_BLOCK",
                               network_entity_id="ocid1.internetgateway.demo")
        network = SimpleNamespace(get_route_table=lambda _: SimpleNamespace(
            data=SimpleNamespace(route_rules=[rule])))
        self.assertFalse(mod.private_network_egress_ready(network, subnet))

    def test_healthy_nat_in_private_subnet_is_eligible(self):
        subnet = SimpleNamespace(
            prohibit_public_ip_on_vnic=True, route_table_id="route",
            vcn_id="vcn")
        rule = SimpleNamespace(destination="0.0.0.0/0",
                               destination_type="CIDR_BLOCK",
                               network_entity_id="ocid1.natgateway.demo")
        network = SimpleNamespace(
            get_route_table=lambda _: SimpleNamespace(
                data=SimpleNamespace(route_rules=[rule])),
            get_nat_gateway=lambda _: SimpleNamespace(
                data=SimpleNamespace(lifecycle_state="AVAILABLE",
                                     vcn_id="vcn", block_traffic=False)))
        self.assertTrue(mod.private_network_egress_ready(network, subnet))

    def test_region_constant_is_home_approved(self):
        self.assertEqual(mod.REGION, "sa-saopaulo-1")
        self.assertEqual((mod.CPU, mod.MEMORY_GB, mod.BOOT_GB), (1, 6, 50))


if __name__ == "__main__":
    unittest.main()
