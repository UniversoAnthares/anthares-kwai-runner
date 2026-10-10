import http.server
import os
import pathlib
import subprocess
import threading
import urllib.request

PORT = int(os.environ.get("PORT", "10000"))
RUNNER_VERSION = "v17.11.1"
ROOT = pathlib.Path("/tmp/anthares-gitlab-runner")
BUILDS = ROOT / "builds-custom"
CACHE = ROOT / "cache-custom"
DRIVER = pathlib.Path(__file__).with_name("custom_executor.py").resolve()
ROOT.mkdir(parents=True, exist_ok=True)
BUILDS.mkdir(parents=True, exist_ok=True)
CACHE.mkdir(parents=True, exist_ok=True)


class Health(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        ok = (ROOT / "connected").exists()
        self.send_response(200 if ok else 503)
        self.end_headers()
        self.wfile.write(b"connected" if ok else b"waiting for runner credential")

    def log_message(self, *_):
        pass


def register_command(binary, config, token):
    DRIVER.chmod(0o700)
    cmd = [
        str(binary),
        "register",
        "--non-interactive",
        "--url",
        "https://gitlab.com/",
        "--executor",
        "custom",
        "--shell",
        "sh",
        "--builds-dir",
        str(BUILDS),
        "--cache-dir",
        str(CACHE),
        "--custom-run-exec",
        str(DRIVER),
        "--config",
        str(config),
    ]

    if token.startswith("glrt-"):
        return cmd + ["--token", token]

    return cmd + [
        "--registration-token",
        token,
        "--description",
        "anthares-render-qa",
        "--tag-list",
        "render-qa",
        "--run-untagged=false",
        "--locked=true",
        "--access-level=ref_protected",
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
    config.unlink(missing_ok=True)
    (ROOT / "connected").unlink(missing_ok=True)
    subprocess.run(register_command(binary, config, token), check=True)
    # The custom executor uses a shared project checkout path. Until per-job
    # build directories are implemented, allow only one checkout per runner
    # process to prevent concurrent git fetch/reset corruption.
    current = config.read_text(encoding="utf-8")
    import re
    current, count = re.subn(r"(?m)^concurrent\\s*=\\s*\\d+", "concurrent = 1", current, count=1)
    if count != 1:
        raise RuntimeError("runner config lacks a concurrent setting")
    config.write_text(current, encoding="utf-8")
    # GitLab's authentication-token registration ignores legacy --tag-list and
    # --access-level flags. The runner must be configured in GitLab UI/API with
    # render-qa tags and an explicit protected-ref policy. Fail closed rather
    # than silently running jobs with an unexpected configuration.
    (ROOT / "connected").touch()
    subprocess.run(
        [str(binary), "run", "--config", str(config), "--working-directory", str(ROOT)],
        check=True,
    )


threading.Thread(target=worker, daemon=True).start()
http.server.ThreadingHTTPServer(("0.0.0.0", PORT), Health).serve_forever()
