import io
import json
import unittest
from unittest.mock import patch
from tools import cortes_linkedin_company_cloud as c


class AuthorizedOrganizationAdminTests(unittest.TestCase):
    def test_valid_admin_of_exact_page(self):
        class Response:
            def __enter__(self): return io.BytesIO(json.dumps({
                "elements": [
                    {"role":"ADMINISTRATOR","state":"APPROVED",
                     "organization":"urn:li:organization:145345334"}
                ]
            }).encode())
            def __exit__(self,*args): return False
        with patch.dict("os.environ",{"LINKEDIN_ACCESS_TOKEN":"secret-test-token"}), \
             patch.object(c.urllib.request,"urlopen",return_value=Response()):
            self.assertIsNone(c.authorize_company_admin())

    def test_different_page_rejected_before_queue(self):
        class Response:
            def __enter__(self): return io.BytesIO(json.dumps({
                "elements":[{"role":"ADMINISTRATOR","state":"APPROVED",
                             "organization":"urn:li:organization:999999"}]
            }).encode())
            def __exit__(self,*args): return False
        with patch.dict("os.environ",{"LINKEDIN_ACCESS_TOKEN":"secret-test-token"}), \
             patch.object(c.urllib.request,"urlopen",return_value=Response()), \
             patch.object(c,"queue") as q:
            with self.assertRaises(c.ConfigRequired):
                c.authorize_company_admin()
            q.assert_not_called()

    def test_non_admin_role_rejected(self):
        class Response:
            def __enter__(self): return io.BytesIO(json.dumps({
                "elements":[{"role":"CONTENT_ADMINISTRATOR","state":"APPROVED",
                             "organization":"urn:li:organization:145345334"}]
            }).encode())
            def __exit__(self,*args): return False
        with patch.dict("os.environ",{"LINKEDIN_ACCESS_TOKEN":"secret-test-token"}), \
             patch.object(c.urllib.request,"urlopen",return_value=Response()):
            with self.assertRaises(c.ConfigRequired):
                c.authorize_company_admin()

if __name__=="__main__":
    unittest.main()
