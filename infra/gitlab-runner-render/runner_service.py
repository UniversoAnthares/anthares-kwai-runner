import http.server
import os
import pathlib
import subprocess
import threading
import urllib.request

PORT = int(os.environ.get("PORT", "10000"))
RUNNER_VERSION = "v17.11.1"
ROOT = pathlib.Path("/tmp/anthares-gitlab-runner")
ROOT.mkdir(parents=True, exist_ok=True)

class Health(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        ok = (ROOT / "connected").exists()
        self.send_response(200 if ok else 503)
        self.end_headers()
        self.wfile.write(b"connected" if ok else b"waiting for runner credential")
    def log_message(self, *_):
        pass

def worker():
    token = os.environ.get("GITLAB_RUNNER_TOKEN", "").strip()
    if not token:
        print("GITLAB_RUNNER_TOKEN missing; runner not connected", flush=True)
        return
    binary = ROOT / "gitlab-runner"
    urllib.request.urlretrieve(
        "https://gitlab-runner-downloads.s3.amazonaws.com/" + RUNNER_VERSION + "/binaries/gitlab-runner-linux-amd64",
        binary,
    )
    binary.chmod(0o700)
    config = ROOT / "config.toml"
    cmd = [str(binary), "register", "--non-interactive",
           "--url", "https://gitlab.com/", "--token", token,
           "--executor", "shell", "--config", str(config)]
    subprocess.run(cmd, check=True)
    (ROOT / "connected").touch()
    subprocess.run([str(binary), "run", "--config", str(config),
                    "--working-directory", str(ROOT)], check=True)

threading.Thread(target=worker, daemon=True).start()
http.server.ThreadingHTTPServer(("0.0.0.0", PORT), Health).serve_forever()
