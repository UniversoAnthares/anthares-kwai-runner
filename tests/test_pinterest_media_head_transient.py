"""Offline Pinterest media HEAD failures: no Buffer write on uncertain origin."""
import ast
from pathlib import Path
import time
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"tools/cortes_buffer_pinterest_cloud.py"
TREE=ast.parse(SRC.read_text(encoding="utf8"))
FUNCTION=next(x for x in TREE.body if isinstance(x,ast.FunctionDef) and x.name=="is_media_missing")
NS={"urllib":urllib,"time":time,"RuntimeError":RuntimeError,"TimeoutError":TimeoutError,"OSError":OSError}
exec(compile(ast.Module(body=[FUNCTION],type_ignores=[]),str(SRC),"exec"),NS)
check=NS["is_media_missing"]
URL="https://anthares.us/wp-content/uploads/valid.mp4"

class Response:
    status=200
    def __enter__(self): return self
    def __exit__(self,*_): return False

def http_error(code):
    return urllib.error.HTTPError(URL,code,"blocked",{},None)

class PinterestOrigin(unittest.TestCase):
    @patch("urllib.request.urlopen")
    def test_head_200_allows_preflight(self,open_):
        open_.return_value=Response()
        self.assertFalse(check(URL))
        self.assertEqual(open_.call_count,1)

    @patch("urllib.request.urlopen")
    def test_true_404_isolated(self,open_):
        open_.side_effect=http_error(404)
        self.assertTrue(check(URL))
        self.assertEqual(open_.call_count,1)

    @patch("time.sleep")
    @patch("urllib.request.urlopen")
    def test_transient_urlerror_recovers(self,open_,sleep):
        open_.side_effect=[urllib.error.URLError("temporary"),Response()]
        self.assertFalse(check(URL))
        self.assertEqual(open_.call_count,2)

    @patch("time.sleep")
    @patch("urllib.request.urlopen")
    def test_exhausted_urlerror_fails_closed(self,open_,sleep):
        open_.side_effect=urllib.error.URLError("temporary")
        with self.assertRaisesRegex(RuntimeError,"TRANSPORT_UNAVAILABLE"):check(URL)
        self.assertEqual(open_.call_count,3)

    @patch("time.sleep")
    @patch("urllib.request.urlopen")
    def test_http_503_retry_then_failclosed(self,open_,sleep):
        open_.side_effect=http_error(503)
        with self.assertRaisesRegex(RuntimeError,"HTTP_UNVERIFIED"):check(URL)
        self.assertEqual(open_.call_count,3)

    @patch("urllib.request.urlopen")
    def test_http_403_never_assumed_available(self,open_):
        open_.side_effect=http_error(403)
        with self.assertRaisesRegex(RuntimeError,"HTTP_UNVERIFIED"):check(URL)
        self.assertEqual(open_.call_count,1)

    @patch("urllib.request.urlopen")
    def test_unsafe_host_never_probed(self,open_):
        self.assertFalse(check("https://evil.example/video.mp4"))
        open_.assert_not_called()

if __name__=="__main__":unittest.main()
