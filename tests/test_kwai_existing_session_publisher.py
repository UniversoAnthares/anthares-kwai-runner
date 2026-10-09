"""Offline contract tests for the existing-session publisher core."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / ".devcontainer" / "kwai-existing-session-publisher.py"
spec = importlib.util.spec_from_file_location("kwai_existing_session_publisher", MODULE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class FakeLocator:
    def __init__(self, *, count=1, visible=True):
        self._count = count
        self._visible = visible
        self.files = []
        self.filled = None
        self.clicked = False
        self.first = self

    async def count(self): return self._count
    async def is_visible(self): return self._visible
    async def set_input_files(self, value): self.files.append(value)
    async def fill(self, value): self.filled = value
    async def click(self): self.clicked = True


class FakePage:
    def __init__(self):
        self.upload = FakeLocator()
        self.textarea = FakeLocator()
        self.editable = FakeLocator(count=0, visible=False)
        self.publish = FakeLocator()

    def locator(self, selector):
        if selector == "input[type=file]": return self.upload
        if selector == "textarea": return self.textarea
        if selector == "[contenteditable=true]": return self.editable
        raise AssertionError(selector)

    def get_by_role(self, role, name=None):
        self.role_request = (role, name)
        return self.publish


class ExistingSessionPublisherTests(unittest.IsolatedAsyncioTestCase):
    def test_authorization_requires_both_independent_gates(self):
        for identity, surface, expected in [
            (False, False, False), (True, False, False),
            (False, True, False), (True, True, True),
        ]:
            self.assertEqual(mod.authorization(identity, surface)["publication_allowed"], expected)

    async def test_prepare_refuses_before_touching_page_without_identity(self):
        page = FakePage()
        with tempfile.NamedTemporaryFile() as media:
            with self.assertRaises(PermissionError):
                await mod.prepare_upload(page, media.name, "x", identity_verified=False,
                                         operational_create_surface=True)
        self.assertEqual(page.upload.files, [])

    async def test_prepare_attaches_media_but_does_not_publish(self):
        page = FakePage()
        with tempfile.NamedTemporaryFile() as media:
            result = await mod.prepare_upload(page, media.name, "caption",
                                              identity_verified=True,
                                              operational_create_surface=True)
        self.assertTrue(result["prepared"])
        self.assertFalse(result["published"])
        self.assertEqual(page.textarea.filled, "caption")
        self.assertFalse(page.publish.clicked)

    async def test_publish_requires_explicit_final_confirmation(self):
        page = FakePage()
        with self.assertRaises(PermissionError):
            await mod.publish_prepared(page, identity_verified=True,
                                       operational_create_surface=True,
                                       final_confirmation=False)
        self.assertFalse(page.publish.clicked)

    async def test_publish_click_only_after_all_gates(self):
        page = FakePage()
        result = await mod.publish_prepared(page, identity_verified=True,
                                            operational_create_surface=True,
                                            final_confirmation=True)
        self.assertTrue(result["publish_click_attempted"])
        self.assertTrue(page.publish.clicked)

    def test_source_never_owns_browser_or_session_state(self):
        source = MODULE.read_text()
        for needle in ("launch(", "launch_persistent_context(", "connect_over_cdp(",
                       "storage_state(", ".cookies(", "screenshot(", "localStorage",
                       "sessionStorage"):
            self.assertNotIn(needle, source, needle)
        self.assertIn("prepare_upload", source)
        self.assertIn("publish_prepared", source)
        self.assertIn("explicit_final_confirmation_required", source)


if __name__ == "__main__":
    unittest.main()
