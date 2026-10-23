"""Offline assertion: actual physical Kwai ACK path invokes supplementary TinyFish safely."""
import importlib.util
import pathlib
import sys
import unittest
from unittest import mock

FILE = pathlib.Path(__file__).resolve().parents[1] / "tools" / "kwai_physical_public_proof.py"


def load_module():
    with mock.patch.dict(sys.modules, {"kwai_native_cortes": mock.Mock()}):
        spec = importlib.util.spec_from_file_location("kwai_physical_public_proof_test", FILE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


class PhysicalProofTinyFishContract(unittest.TestCase):
    def test_actual_recover_path_has_the_public_read_hook(self):
        module = load_module()
        self.assertIn("_supplementary_public_read", module.recover.__code__.co_names)

    def test_adapter_is_supplementary_with_https_fallback(self):
        module = load_module()
        with mock.patch.dict(sys.modules, {"tinyfish_public_probe": mock.Mock(
            probe_public_page=mock.Mock(return_value={"ok": True, "provider": "tinyfish_fetch"})
        )}) as registered:
            result = module._supplementary_public_read("https://k.kwai.com/p/ABC123", "lucasrosalem")
            self.assertTrue(result["ok"])
            registered["tinyfish_public_probe"].probe_public_page.assert_called_once_with(
                "https://k.kwai.com/p/ABC123", ("lucasrosalem",), fallback=True, timeout=6,
                allowed_hosts=("k.kwai.com", "www.kwai.com"),
            )

    def test_provider_failure_does_not_block_physical_evidence(self):
        module = load_module()
        with mock.patch.dict(sys.modules, {"tinyfish_public_probe": mock.Mock(
            probe_public_page=mock.Mock(side_effect=TimeoutError("provider unavailable"))
        )}):
            result = module._supplementary_public_read("https://k.kwai.com/p/ABC123", "lucasrosalem")
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "supplementary_read_unavailable")


if __name__ == "__main__":
    unittest.main()
