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

    def _locked_public_network(self, source="203.0.113.7/32", port=22,
                               ingress_count=1):
        subnet = SimpleNamespace(
            prohibit_public_ip_on_vnic=False, route_table_id="route",
            vcn_id="vcn", security_list_ids=["sec"])
        default = SimpleNamespace(destination="0.0.0.0/0",
                                  destination_type="CIDR_BLOCK",
                                  network_entity_id="ocid1.internetgateway.demo")
        tcp = SimpleNamespace(destination_port_range=SimpleNamespace(
            min=port, max=port))
        rule = SimpleNamespace(source=source, protocol="6", is_stateless=False,
                               source_type="CIDR_BLOCK", tcp_options=tcp)
        egress = SimpleNamespace(destination="0.0.0.0/0", protocol="all",
                                 destination_type="CIDR_BLOCK")
        network = SimpleNamespace(
            get_route_table=lambda _: SimpleNamespace(
                data=SimpleNamespace(route_rules=[default])),
            get_internet_gateway=lambda _: SimpleNamespace(
                data=SimpleNamespace(lifecycle_state="AVAILABLE",
                                     vcn_id="vcn", is_enabled=True)),
            get_security_list=lambda _: SimpleNamespace(
                data=SimpleNamespace(ingress_security_rules=[rule] * ingress_count,
                                     egress_security_rules=[egress]))
        )
        return network, subnet

    def test_locked_public_igw_allows_safe_free_egress(self):
        network, subnet = self._locked_public_network()
        self.assertEqual(mod.safe_instance_network_mode(network, subnet),
                         "LOCKED_PUBLIC")

    def test_public_ssh_open_range_is_denied(self):
        network, subnet = self._locked_public_network(source="0.0.0.0/0")
        self.assertIsNone(mod.safe_instance_network_mode(network, subnet))

    def test_public_extra_ingress_is_denied(self):
        network, subnet = self._locked_public_network(ingress_count=2)
        self.assertIsNone(mod.safe_instance_network_mode(network, subnet))

    def test_public_unexpected_port_is_denied(self):
        network, subnet = self._locked_public_network(port=5555)
        self.assertIsNone(mod.safe_instance_network_mode(network, subnet))

    def _stub_cloud_init(self, fake_path, content):
        reader = (fake_path.return_value.resolve.return_value
                  .parents.__getitem__.return_value.__truediv__.return_value)
        reader.read_bytes.return_value = content

    def _valid_cloud_init(self):
        return (b"#cloud-config\n--privileged\n127.0.0.1:5555:5555\n"
                + b'--platform "$PLATFORM"\n'
                + b'/etc/modules-load.d/anthares-redroid.conf\n'
                + b'options binder_linux devices=binder,hwbinder,vndbinder\n'
                + b'docker start anthares-redroid\n'
                + mod.REDROID_ARM64_IMAGE.encode("ascii")
                + b"\n" + mod.REDROID_AMD64_IMAGE.encode("ascii"))

    def _assert_bootstrap_rejected(self, data):
        with patch.object(mod, "Path") as path:
            self._stub_cloud_init(path, data)
            with self.assertRaises(ValueError):
                mod.redroid_cloud_init_data()

    def test_cloud_init_is_encoded_and_local_only(self):
        import base64
        data = self._valid_cloud_init()
        with patch.object(mod, "Path") as path:
            self._stub_cloud_init(path, data)
            self.assertEqual(base64.b64decode(
                mod.redroid_cloud_init_data()), data)

    def test_cloud_init_rejects_missing_amd64_digest(self):
        data = self._valid_cloud_init().replace(
            mod.REDROID_AMD64_IMAGE.encode("ascii"), b"MISSING_AMD64")
        self._assert_bootstrap_rejected(data)

    def test_cloud_init_rejects_hardcoded_platform(self):
        data = self._valid_cloud_init().replace(
            b'--platform "$PLATFORM"', b"--platform linux/arm64")
        self._assert_bootstrap_rejected(data)

    def test_cloud_init_rejects_missing_persistent_binder(self):
        data = self._valid_cloud_init().replace(
            b"/etc/modules-load.d/anthares-redroid.conf", b"UNCONFIGURED")
        self._assert_bootstrap_rejected(data)

    def test_cloud_init_rejects_missing_container_recovery(self):
        data = self._valid_cloud_init().replace(
            b"docker start anthares-redroid", b"CONTAINER_RECOVERY_MISSING")
        self._assert_bootstrap_rejected(data)

    def test_cloud_init_rejects_mutable_redroid_tag(self):
        data = self._valid_cloud_init().replace(
            mod.REDROID_ARM64_IMAGE.encode("ascii"),
            b"redroid/redroid:12.0.0_64only-240527")
        self._assert_bootstrap_rejected(data)

    def test_cloud_init_rejects_public_adb_binding(self):
        data = self._valid_cloud_init().replace(
            b"127.0.0.1:5555:5555", b"0.0.0.0:5555:5555")
        self._assert_bootstrap_rejected(data)

    def test_cloud_init_rejects_missing_header(self):
        data = self._valid_cloud_init().replace(
            b"#cloud-config\n", b"BAD_HEADER\n")
        self._assert_bootstrap_rejected(data)

    def test_launch_retry_token_is_stable_and_scope_specific(self):
        from uuid import UUID
        first = mod.launch_retry_token("tenancy-a", "subnet-a")
        self.assertEqual(UUID(first).version, 5)
        self.assertEqual(first, mod.launch_retry_token("tenancy-a", "subnet-a"))
        self.assertNotEqual(first, mod.launch_retry_token("tenancy-b", "subnet-a"))
        self.assertNotEqual(first, mod.launch_retry_token("tenancy-a", "subnet-b"))

    def test_guarded_launch_passes_stable_oci_retry_token(self):
        from unittest.mock import Mock
        compute = Mock()
        request = object()
        mod.guarded_launch(compute, request, "tenancy-a", "subnet-a")
        compute.launch_instance.assert_called_once_with(
            request, opc_retry_token=mod.launch_retry_token(
                "tenancy-a", "subnet-a"))

    def _approved_subnet_fixture(self):
        return SimpleNamespace(
            id="ocid1.subnet.oc1.sa-saopaulo-1.example",
            display_name=mod.APPROVED_SUBNET_NAME,
            compartment_id="tenancy",
            cidr_block=mod.APPROVED_SUBNET_CIDR,
            lifecycle_state="AVAILABLE",
        )

    def test_pin_existing_ssh_public_key_and_reject_substitution(self):
        import base64
        import hashlib
        raw = b"synthetic-ed25519-public-material-for-fixture"
        encoded = base64.b64encode(raw).decode("ascii")
        digest = "SHA256:" + base64.b64encode(
            hashlib.sha256(raw).digest()).decode("ascii").rstrip("=")
        reader = (
            "ssh-ed25519 " + encoded + " fixture"
        )
        with patch.object(mod, "Path") as path, patch.object(
                mod, "APPROVED_SSH_KEY_SHA256", digest):
            selected = (path.return_value.resolve.return_value
                        .parents.__getitem__.return_value.__truediv__.return_value)
            selected.read_text.return_value = reader
            self.assertEqual(
                mod.approved_ssh_public_key(),
                "ssh-ed25519 " + encoded + " anthares-oci-admin"
            )
            selected.read_text.return_value = "ssh-ed25519 AAAASUBSTITUTED"
            with self.assertRaises(ValueError):
                mod.approved_ssh_public_key()

    def test_approved_subnet_is_discovered_without_secret_ocid(self):
        subnet = self._approved_subnet_fixture()
        network = SimpleNamespace(
            list_subnets=lambda **kwargs: None,
            get_subnet=lambda _id: SimpleNamespace(data=subnet)
        )
        with patch.object(mod, "pages", return_value=[subnet]) as pages:
            self.assertIs(mod.approved_subnet(network, "tenancy"), subnet)
            pages.assert_called_once()
        with patch.object(mod, "pages", return_value=[subnet]):
            with self.assertRaisesRegex(ValueError, "SUBNET_OVERRIDE"):
                mod.approved_subnet(network, "tenancy", "different-subnet")

    def test_unapproved_or_multiple_subnet_blocks_launch(self):
        subnet = self._approved_subnet_fixture()
        network = SimpleNamespace(list_subnets=lambda **kwargs: None)
        with patch.object(mod, "pages", return_value=[subnet, subnet]):
            with self.assertRaisesRegex(ValueError, "NOT_UNIQUE"):
                mod.approved_subnet(network, "tenancy")
        bad = self._approved_subnet_fixture()
        bad.cidr_block = "10.92.7.0/24"
        with patch.object(mod, "pages", return_value=[bad]):
            with self.assertRaisesRegex(ValueError, "NOT_UNIQUE"):
                mod.approved_subnet(network, "tenancy")

    def test_approved_boot_access_rejects_ssh_key_override(self):
        subnet = self._approved_subnet_fixture()
        sshkey = "ssh-ed25519 AAAA_APPROVED anthares-oci-admin"
        with patch.object(mod, "approved_subnet", return_value=subnet), \
             patch.object(mod, "approved_ssh_public_key", return_value=sshkey), \
             patch.object(mod, "safe_instance_network_mode", return_value="LOCKED_PUBLIC"):
            result = mod.approved_boot_access({}, "tenancy", {})
            self.assertEqual(result, (subnet, sshkey, "LOCKED_PUBLIC"))
            with self.assertRaisesRegex(ValueError, "SSH_KEY_OVERRIDE"):
                mod.approved_boot_access({}, "tenancy", {
                    "ssh_public_key": "ssh-ed25519 AAAA_WRONG intruder"})

    def test_preflight_runs_even_when_a1_host_out_of_capacity(self):
        from unittest.mock import Mock
        signer = dict(tenancy="tenancy")
        compute, network, block, identity = Mock(), Mock(), Mock(), Mock()
        region = SimpleNamespace(region_name=mod.REGION, status="READY")
        ad = SimpleNamespace(name="AD-1")
        shape = SimpleNamespace(
            instance_shape=mod.A1, availability_status="OUT_OF_HOST_CAPACITY")
        compute.create_compute_capacity_report.return_value.data.shape_availabilities = [shape]
        subnet = self._approved_subnet_fixture()
        with patch.object(mod, "auth", return_value=(
                signer, compute, network, block, identity)), \
             patch.object(mod, "pages", side_effect=[[region], [ad]]), \
             patch.object(mod, "approved_boot_access",
                          return_value=(subnet, "ssh-ed25519 AAAA_PUBLIC", "LOCKED_PUBLIC")
                          ) as preflight:
            self.assertEqual(mod.main(), 0)
            preflight.assert_called_once_with(network, "tenancy", signer)
            compute.launch_instance.assert_not_called()

    def test_region_constant_is_home_approved(self):
        self.assertEqual(mod.REGION, "sa-saopaulo-1")
        self.assertEqual((mod.CPU, mod.MEMORY_GB, mod.BOOT_GB), (1, 6, 50))


if __name__ == "__main__":
    unittest.main()
