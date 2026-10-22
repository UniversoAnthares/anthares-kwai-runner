import pathlib
import unittest
import yaml

ROOT=pathlib.Path(__file__).resolve().parents[1]
class XCloudPreflightSecretGuardsTests(unittest.TestCase):
    def test_secrets_validated_before_browser_install(self):
        for filename, job in [
            ("x-codeberg-auth-identity.yml","authenticated-identity"),
            ("x-codeberg-primary.yml","publish"),
        ]:
            p=ROOT/".forgejo/workflows"/filename
            raw=p.read_text(encoding="utf-8")
            obj=yaml.safe_load(raw)
            steps=obj["jobs"][job]["steps"]
            guard=next(i for i,x in enumerate(steps) if "secret" in x.get("name","").lower() or "credential" in x.get("name","").lower())
            browser=next(i for i,x in enumerate(steps) if "playwright install" in str(x.get("run","")))
            self.assertLess(guard,browser)
            self.assertIn('X_CODEBERG_REQUIRED_SECRET_MISSING=ARA_SHARED',raw)
            self.assertNotIn('echo "$ARA_SHARED"',raw)

    def test_identity_probe_reports_only_sanitized_state(self):
        s=(ROOT/"tools/x_cloud_browser_identity_probe.py").read_text(encoding="utf8")
        self.assertIn("X_CLOUD_BROWSER_DOM_DIAG=",s)
        self.assertIn("switcherPresent",s)
        self.assertIn("composerPresent",s)
        self.assertIn("route: location.pathname",s)
        self.assertIn("time.monotonic() + 45",s)
        self.assertNotIn("document.body.innerText",s)
if __name__=="__main__":unittest.main()
