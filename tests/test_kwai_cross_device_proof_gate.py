#!/usr/bin/env python3
"""Offline proof contract tests. Never calls Android, Kwai or the queue."""
import ast
import json
import pathlib
import re
import tempfile
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]


class KwaiCrossDeviceProofTests(unittest.TestCase):
    def test_independent_reader_and_media_state_precede_proof(self):
        source=(ROOT/"tools/kwai_physical_public_proof.py").read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn("kwai_verify_public_post.py",source)
        self.assertIn("cross.get('title_match') is True",source)
        self.assertIn("state.get('media_sha256')",source)
        self.assertIn("verified_publication_job_id",source)
        self.assertIn("kwai_independent_cross_device_media_bound_v1",source)
        self.assertNotIn("clipboard-copy-prohibited-use-direct-share-proof",source)
        self.assertIn("k.tap(serial,copy[0])",source)

    def test_central_ack_rejects_wrong_and_legacy_proofs(self):
        src=(ROOT/"tools/kwai_physical_queue_daemon.py").read_text(encoding="utf-8")
        tree=ast.parse(src)
        node=next(f for f in tree.body if isinstance(f,ast.FunctionDef) and f.name=="evidence")
        fn=compile(ast.Module(body=[node],type_ignores=[]),"<kwai-evidence>","exec")
        job="kwai-identity-g1-source-10-40"
        digest="a"*64
        state={"caption":"Identidade da live verificada","media_sha256":digest}
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp)
            dest=root/".state"/"kwai-memu-evidence"/job
            dest.mkdir(parents=True)
            good={
                "ok":True,"public_url":"https://k.kwai.com/p/AbCD1234",
                "expected_account":"lucasrosalem",
                "kind":"kwai_independent_cross_device_media_bound_v1",
                "verified_publication_job_id":job,
                "caption":state["caption"],
                "media_sha256":digest,
                "cross_device_proof":{"ok":True,"public_url":"https://k.kwai.com/p/AbCD1234",
                     "title_match":True,"expected_account":"lucasrosalem"}
            }
            env={"ROOT":root,"EXPECTED_ACCOUNT":"lucasrosalem",
                 "re":re,"json":json,"pubstate":lambda _:state}
            exec(fn,env)
            def run(proof):
                (dest/"public-link-proof.json").write_text(json.dumps(proof),encoding="utf-8")
                return env["evidence"](job)
            self.assertEqual(run(good)["remote_id"],good["public_url"])
            for label,bad in (
                ("legacy",{"ok":True,"public_url":good["public_url"],
                    "expected_account":"lucasrosalem"}),
                ("job",{**good,"verified_publication_job_id":"other-job"}),
                ("caption",{**good,"caption":"wrong video"}),
                ("media",{**good,"media_sha256":"b"*64}),
                ("title",{**good,"cross_device_proof":{**good["cross_device_proof"],"title_match":False}}),
                ("url",{**good,"cross_device_proof":{**good["cross_device_proof"],"public_url":"https://k.kwai.com/p/OtherAAA"}})
            ):
                with self.subTest(label=label),self.assertRaises(RuntimeError):
                    run(bad)


if __name__=="__main__":
    unittest.main()
