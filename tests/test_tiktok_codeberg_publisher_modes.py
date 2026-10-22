import ast, pathlib,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
class CodebergPublishingGateTests(unittest.TestCase):
    def test_secondary_signed_neon_status_before_write_gate(self):
        src=(ROOT/"tools"/"cortes_tiktok_lucasrosalem4_cloud_publish.py").read_text(encoding="utf-8")
        ast.parse(src)
        self.assertLess(src.index('if os.environ.get("CODEBERG_NEON_AUTH_PROBE")'),
                        src.index('if os.environ.get("TIKTOK_LUCASROSALEM4_CLOUD_ENABLED"'))
        self.assertIn('verified=call("status",token)',src)
    def test_primary_never_uses_vault_secret_in_codeberg(self):
        src=(ROOT/"tools"/"cortes_tiktok_hosted_publish.py").read_text(encoding="utf-8")
        ast.parse(src)
        self.assertIn('os.getenv("CORTES_CODEBERG_RUNTIME")=="true"',src)
        self.assertIn('state,meta=load_canonical_state()',src)
        self.assertLess(src.index('TIKTOK_CODEBERG_UNIVERSO_ENABLED'),src.index('claim=q.qcall("claim"'))
    def test_workflow_source_gates(self):
        for account,filename in (
            ("lucas4","cortes-tiktok-lucas4-codeberg.yml"),
            ("universo","cortes-tiktok-universo-codeberg.yml")
        ):
            src=(ROOT/".forgejo"/"workflows"/filename).read_text(encoding="utf-8")
            self.assertIn("enable-openid-connect: true",src)
            self.assertIn("codeberg-medium",src)
            self.assertIn("vars.TIKTOK_CODEBERG_",src)
            self.assertIn("persist-credentials: false",src)
            self.assertNotIn("ARA_SHARED",src)
            self.assertNotIn("DATABASE_URL",src)
    def test_neon_workflow_paths_are_exact(self):
        for account,fn in (
            ("lucas4","neon-cortes-lucasrosalem4"),
            ("universo","neon-cortes-tiktok")
        ):
            src=(ROOT/"infra"/fn/"index.mjs").read_text(encoding="utf-8")
            self.assertIn("cortes-tiktok-"+account+"-codeberg.yml",src)
if __name__=="__main__": unittest.main()
