"""Regression suite for the read-only Android cloud VPS qualification gate."""
import unittest

from tools import redroid_free_vps_preflight as target


def good():
    return {
        "arch": "x86_64",
        "cpus": 2,
        "memory_mib": 4096,
        "disk_free_gib": 50,
        "root": True,
        "virtualization": "kvm",
        "binder_probe": "KERNEL_MODULE_FOUND",
        "docker_cli_installed": False,
        "os": "Linux",
    }


class FreeVpsPreflightTests(unittest.TestCase):
    def test_kvm_candidate_never_claims_redroid_running(self):
        result = target.assess(good())
        self.assertEqual(result["status"], "CANDIDATE_FOR_ISOLATED_INSTALL_TEST")
        self.assertEqual(result["failures"], [])
        self.assertIn("ACTUAL_BINDER_DEVICE_CREATION_AND_ANDROID_BOOT",
                      result["mandatory_unverified"])
        self.assertIn("PROVIDER_TRUST_AND_ZERO_COST",
                      result["mandatory_unverified"])

    def test_no_binder_requires_kernel_proof(self):
        host = good()
        host["binder_probe"] = "UNVERIFIED"
        self.assertEqual(target.assess(host)["status"], "BINDER_PROOF_REQUIRED")

    def test_small_nanokvm_vm_is_rejected(self):
        host = good()
        host.update(cpus=1, memory_mib=2048, disk_free_gib=10)
        result = target.assess(host)
        self.assertEqual(result["status"], "REJECTED")
        self.assertIn("INSUFFICIENT_VCPU", result["failures"])
        self.assertIn("INSUFFICIENT_MEMORY", result["failures"])
        self.assertIn("INSUFFICIENT_FREE_DISK", result["failures"])

    def test_no_root_rejected(self):
        host = good()
        host["root"] = False
        self.assertIn("ROOT_REQUIRED", target.assess(host)["failures"])

    def test_lxc_rejected_even_as_root(self):
        host = good()
        host["virtualization"] = "lxc"
        self.assertIn("HOST_KERNEL_CONTROL_UNAVAILABLE_OR_UNPROVEN",
                      target.assess(host)["failures"])

    def test_arch_and_os_rejected(self):
        host = good()
        host.update(arch="i686", os="Windows")
        self.assertEqual(target.assess(host)["status"], "REJECTED")
        self.assertIn("LINUX_REQUIRED", target.assess(host)["failures"])

    def test_bootstrap_remains_unproven_if_docker_is_installed(self):
        host = good()
        host["docker_cli_installed"] = True
        self.assertIn("ACTUAL_PRIVILEGED_DOCKER_EXECUTION",
                      target.assess(host)["mandatory_unverified"])


if __name__ == "__main__":
    unittest.main()
