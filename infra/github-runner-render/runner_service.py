import http.server
import os
import pathlib
import subprocess
import tarfile
import threading
import urllib.request

PORT = int(os.environ.get("PORT", "10000"))
VERSION = os.environ.get("GITHUB_RUNNER_VERSION", "2.337.0")
ROOT = pathlib.Path("/tmp/anthares-github-runner")
ROOT.mkdir(parents=True, exist_ok=True)

class Health(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        ready = (ROOT / "configured").exists()
        self.send_response(200 if ready else 503)
        self.end_headers()
        self.wfile.write(b"configured" if ready else b"starting")
    def log_message(self, *_):
        pass

def worker():
    token = os.environ.get("GITHUB_RUNNER_REG_TOKEN", "").strip()
    repo = os.environ.get("GITHUB_REPO", "UniversoAnthares/anthares-clipper").strip()
    labels = os.environ.get("GITHUB_RUNNER_LABELS", "render-cloudflare").strip()
    if not token:
        print("GITHUB_RUNNER_REG_TOKEN missing", flush=True)
        return
    url = f"https://github.com/actions/runner/releases/download/v{VERSION}/actions-runner-linux-x64-{VERSION}.tar.gz"
    archive = ROOT / "runner.tgz"
    urllib.request.urlretrieve(url, archive)
    with tarfile.open(archive, "r:gz") as tf:
        tf.extractall(ROOT, filter="data")
    cfg = [
        str(ROOT / "config.sh"), "--unattended", "--ephemeral", "--replace",
        "--url", f"https://github.com/{repo}", "--token", token,
        "--name", "anthares-render-cloudflare", "--labels", labels,
        "--work", "_work",
    ]
    subprocess.run(cfg, cwd=ROOT, check=True)
    (ROOT / "configured").touch()
    print("GITHUB_RUNNER_CONFIGURED=1", flush=True)
    subprocess.run([str(ROOT / "run.sh")], cwd=ROOT, check=False)

threading.Thread(target=worker, daemon=True).start()
http.server.ThreadingHTTPServer(("0.0.0.0", PORT), Health).serve_forever()
