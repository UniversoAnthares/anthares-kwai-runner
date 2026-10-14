import http.server
import os
import pathlib
import re
import subprocess
import threading
import time
import urllib.request

PORT = int(os.environ.get("PORT", "10000"))
RUNNER_VERSION = "v17.11.1"
ROOT = pathlib.Path("/tmp/anthares-gitlab-runner")
BUILDS = ROOT / "builds-custom"
CACHE = ROOT / "cache-custom"
DRIVER = pathlib.Path(__file__).with_name("custom_executor.py").resolve()
CONNECTED = ROOT / "connected"
ROOT.mkdir(parents=True, exist_ok=True)
BUILDS.mkdir(parents=True, exist_ok=True)
CACHE.mkdir(parents=True, exist_ok=True)

_runner_lock = threading.Lock()
_runner_process = None


def runner_alive():
    with _runner_lock:
        return _runner_process is not None and _runner_process.poll() is None


class Health(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        ok = CONNECTED.exists() and runner_alive()
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
        "--run-untagged=true",
        "--locked=true",
        "--access-level=ref_protected",
    ]


def prepare_runner(binary, config, token):
    config.unlink(missing_ok=True)
    CONNECTED.unlink(missing_ok=True)
    subprocess.run(register_command(binary, config, token), check=True)
    current = config.read_text(encoding="utf-8")
    current, count = re.subn(r"(?m)^concurrent\s*=\s*\d+", "concurrent = 1", current, count=1)
    if count != 1:
        raise RuntimeError("runner config lacks a concurrent setting")
    if "[runners.custom]" not in current:
        raise RuntimeError("runner config lacks custom executor section")
    current = current.replace(
        "[runners.custom]",
        '[runners.custom]\n  config_exec = "' + str(DRIVER) + '"\n  config_args = ["config"]',
        1,
    )
    config.write_text(current, encoding="utf-8")


def worker():
    global _runner_process
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

    while True:
        try:
            prepare_runner(binary, config, token)
            process = subprocess.Popen(
                [str(binary), "run", "--config", str(config), "--working-directory", str(ROOT)]
            )
            with _runner_lock:
                _runner_process = process
            CONNECTED.touch()
            print("GitLab runner connected", flush=True)
            code = process.wait()
            print(f"GitLab runner exited with code {code}; restarting", flush=True)
        except Exception as exc:
            print(f"GitLab runner bootstrap failed: {type(exc).__name__}: {exc}", flush=True)
        finally:
            CONNECTED.unlink(missing_ok=True)
            with _runner_lock:
                _runner_process = None
        time.sleep(5)


threading.Thread(target=worker, daemon=True).start()
http.server.ThreadingHTTPServer(("0.0.0.0", PORT), Health).serve_forever()
