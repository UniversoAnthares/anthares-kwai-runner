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


def register_command(binary, config, token):
    cmd = [
        str(binary),
        "register",
        "--non-interactive",
        "--url",
        "https://gitlab.com/",
        "--executor",
        "shell",
        "--config",
        str(config),
    ]

    if token.startswith("glrt-"):
        return cmd + ["--token", token]

    # Keep the runner project-scoped, locked and tag-only. QA/MR branches may
    # execute on it, while GitLab protected variables remain unavailable to
    # unprotected refs.
    return cmd + [
        "--registration-token",
        token,
        "--description",
        "anthares-render-qa",
        "--tag-list",
        "render-qa",
        "--run-untagged=false",
        "--locked=true",
        "--access-level=not_protected",
    ]


def worker():
    token = os.environ.get("GITLAB_RUNNER_TOKEN", "").strip()
    if not token:
        print("GITLAB_RUNNER_TOKEN missing; runner not connected", flush=True)
        return

    binary = ROOT / "gitlab-runner"
    urllib.request.urlretrieve(
        "https://gitlab-runner-downloads.s3.amazonaws.com/"
        + RUNNER_VERSION
        + "/binaries/gitlab-runner-linux-amd64",
        binary,
    )
    binary.chmod(0o700)
    config = ROOT / "config.toml"
    subprocess.run(register_command(binary, config, token), check=True)
    (ROOT / "connected").touch()
    subprocess.run(
        [str(binary), "run", "--config", str(config), "--working-directory", str(ROOT)],
        check=True,
    )


threading.Thread(target=worker, daemon=True).start()
http.server.ThreadingHTTPServer(("0.0.0.0", PORT), Health).serve_forever()
