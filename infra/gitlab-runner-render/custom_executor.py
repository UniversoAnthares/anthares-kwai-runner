#!/usr/bin/env python3
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request
import urllib.parse

TOOLS_ROOT = pathlib.Path("/tmp/anthares-gitlab-custom-tools")
JOBS_ROOT = pathlib.Path("/tmp/anthares-gitlab-custom-jobs")
RUNNER_ROOT = pathlib.Path("/tmp/anthares-gitlab-runner")
BUILDS_ROOT = RUNNER_ROOT / "builds-custom"
CACHE_ROOT = RUNNER_ROOT / "cache-custom"

UDOCKER_VERSION = "1.3.17"
UDOCKER_URL = (
    "https://github.com/indigo-dc/udocker/releases/download/"
    f"{UDOCKER_VERSION}/udocker-{UDOCKER_VERSION}.tar.gz"
)
CRANE_VERSION = "v0.22.1"
CRANE_URL = (
    "https://github.com/google/go-containerregistry/releases/download/"
    f"{CRANE_VERSION}/go-containerregistry_Linux_x86_64.tar.gz"
)
CRANE_SHA256 = "0ab7a1d6932a213aed964ce97666c3077fe691c8606413674a8b3e0b9ec4cda0"

ALLOWED_IMAGES = {
    "php:8.5-cli",
    "node:22-bookworm-slim",
    "alpine:3.20",
    "composer:2",
    "python:3.12-alpine",
    "ubuntu:24.04",
}
BASH_IMAGES = {"php:8.5-cli", "node:22-bookworm-slim", "ubuntu:24.04"}
CONTAINER_STAGES = {"build_script", "step_script", "after_script"}
HOST_STAGE_TIMEOUT = 180
IMAGE_META_TIMEOUT = 60
IMAGE_EXPORT_TIMEOUT = 180
IMAGE_EXPORT_ATTEMPTS = 3
LOCAL_PREP_TIMEOUT = 180
CONTAINER_RUN_TIMEOUT = 1200


def _build_failure_code() -> int:
    try:
        return int(os.environ.get("BUILD_FAILURE_EXIT_CODE", "1"))
    except ValueError:
        return 1


def _run(cmd, *, env=None, stdin=None, capture=False, timeout=None):
    kwargs = {"env": env, "stdin": stdin, "check": False, "timeout": timeout}
    if capture:
        kwargs.update({"stdout": subprocess.PIPE, "stderr": subprocess.PIPE, "text": True})
    return subprocess.run(cmd, **kwargs)


def _sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download(url: str, destination: pathlib.Path) -> None:
    tmp = destination.with_suffix(destination.suffix + ".tmp")
    tmp.unlink(missing_ok=True)
    with urllib.request.urlopen(url, timeout=60) as response, tmp.open("wb") as out:
        shutil.copyfileobj(response, out)
    tmp.replace(destination)


def _ensure_tools():
    TOOLS_ROOT.mkdir(parents=True, exist_ok=True)
    JOBS_ROOT.mkdir(parents=True, exist_ok=True)
    BUILDS_ROOT.mkdir(parents=True, exist_ok=True)
    CACHE_ROOT.mkdir(parents=True, exist_ok=True)

    udocker_dir = TOOLS_ROOT / f"udocker-{UDOCKER_VERSION}"
    udocker_bin = udocker_dir / "udocker" / "udocker"
    if not udocker_bin.exists():
        archive = TOOLS_ROOT / f"udocker-{UDOCKER_VERSION}.tar.gz"
        _download(UDOCKER_URL, archive)
        with tarfile.open(archive, "r:gz") as tf:
            tf.extractall(TOOLS_ROOT, filter="data")
        if not udocker_bin.exists():
            raise RuntimeError("udocker archive did not contain the expected executable")

    crane_bin = TOOLS_ROOT / "crane"
    if not crane_bin.exists():
        archive = TOOLS_ROOT / f"crane-{CRANE_VERSION}.tar.gz"
        _download(CRANE_URL, archive)
        if _sha256(archive) != CRANE_SHA256:
            archive.unlink(missing_ok=True)
            raise RuntimeError("crane release checksum mismatch")
        with tarfile.open(archive, "r:gz") as tf:
            member = tf.getmember("crane")
            tf.extract(member, TOOLS_ROOT, filter="data")
        crane_bin.chmod(0o700)

    return udocker_bin, crane_bin


def _job_root() -> pathlib.Path:
    job_id = os.environ.get("CUSTOM_ENV_CI_JOB_ID", "unknown")
    if not job_id.isdigit():
        raise RuntimeError("invalid CI job id")
    root = JOBS_ROOT / job_id
    root.mkdir(parents=True, exist_ok=True)
    return root


def _reset_workspace() -> None:
    raw = os.environ.get("CUSTOM_ENV_CI_PROJECT_DIR", "").strip()
    if not raw:
        return
    project_dir = pathlib.Path(raw).resolve()
    builds_root = BUILDS_ROOT.resolve()
    if project_dir == builds_root or builds_root not in project_dir.parents:
        raise RuntimeError("refusing to reset workspace outside controlled builds root")
    shutil.rmtree(project_dir, ignore_errors=True)
    project_dir.mkdir(parents=True, exist_ok=True)
    print(f"Anthares custom executor: reset workspace {project_dir}", flush=True)

    # The custom executor does not receive the Docker executor's preconfigured
    # Git remote. GitLab's generated get_sources script fetches origin directly.
    project_path = os.environ.get("CUSTOM_ENV_CI_PROJECT_PATH", "").strip()
    job_token = os.environ.get("CUSTOM_ENV_CI_JOB_TOKEN", "").strip()
    server_host = os.environ.get("CUSTOM_ENV_CI_SERVER_HOST", "gitlab.com").strip()
    if not project_path or not job_token or server_host != "gitlab.com":
        raise RuntimeError("missing GitLab job checkout credentials or unexpected host")
    if any(part in ("", ".", "..") for part in project_path.split("/")):
        raise RuntimeError("invalid GitLab project path")
    safe_path = "/".join(urllib.parse.quote(part, safe="") for part in project_path.split("/"))
    safe_token = urllib.parse.quote(job_token, safe="")
    remote_url = f"https://gitlab-ci-token:{safe_token}@{server_host}/{safe_path}.git"
    subprocess.run(["git", "init", "-q", str(project_dir)], check=True)
    subprocess.run(
        ["git", "-C", str(project_dir), "remote", "add", "origin", remote_url],
        check=True,
    )
    print("Anthares custom executor: authenticated origin prepared", flush=True)


def _image_config(crane_bin: pathlib.Path, image: str) -> dict:
    try:
        result = _run(
            [str(crane_bin), "config", "--platform", "linux/amd64", image],
            capture=True,
            timeout=IMAGE_META_TIMEOUT,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"image metadata timed out for {image}") from exc
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"failed to read image config for {image}")
    return json.loads(result.stdout)


def _export_rootfs(crane_bin: pathlib.Path, image: str, rootfs: pathlib.Path) -> None:
    last_error = "unknown export failure"
    for attempt in range(1, IMAGE_EXPORT_ATTEMPTS + 1):
        rootfs.unlink(missing_ok=True)
        print(
            f"Anthares custom executor: exporting image={image} attempt={attempt}/{IMAGE_EXPORT_ATTEMPTS}",
            flush=True,
        )
        try:
            result = _run(
                [str(crane_bin), "export", "--platform", "linux/amd64", image, str(rootfs)],
                capture=True,
                timeout=IMAGE_EXPORT_TIMEOUT,
            )
            if result.returncode == 0 and rootfs.exists() and rootfs.stat().st_size > 0:
                return
            last_error = (result.stderr or result.stdout or "crane export failed").strip()
        except subprocess.TimeoutExpired:
            last_error = f"timed out after {IMAGE_EXPORT_TIMEOUT}s"
        rootfs.unlink(missing_ok=True)
        if attempt < IMAGE_EXPORT_ATTEMPTS:
            time.sleep(2 * attempt)
    raise RuntimeError(f"failed to export rootfs for {image}: {last_error}")


def _checked_local(cmd, *, env=None, label: str):
    try:
        result = _run(cmd, env=env, timeout=LOCAL_PREP_TIMEOUT)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"{label} timed out after {LOCAL_PREP_TIMEOUT}s") from exc
    if result.returncode != 0:
        raise RuntimeError(f"{label} failed")
    return result


def _prepare_container(image: str):
    if image not in ALLOWED_IMAGES:
        raise RuntimeError(f"job image is not allowlisted: {image}")

    udocker_bin, crane_bin = _ensure_tools()
    root = _job_root()
    udocker_home = root / "udocker"
    env = os.environ.copy()
    env["UDOCKER_DIR"] = str(udocker_home)
    container_name = "jobenv"
    marker = root / "prepared.json"

    if marker.exists():
        metadata = json.loads(marker.read_text(encoding="utf-8"))
        if metadata.get("image") == image:
            return udocker_bin, env, container_name, metadata

    _checked_local([str(udocker_bin), "install"], env=env, label="udocker install")
    image_cfg = _image_config(crane_bin, image)
    rootfs = root / "rootfs.tar"
    _export_rootfs(crane_bin, image, rootfs)

    repo_name = "anthares/job:runtime"
    try:
        _checked_local(
            [str(udocker_bin), "import", "--platform=linux/amd64", str(rootfs), repo_name],
            env=env,
            label=f"udocker import for {image}",
        )
    finally:
        rootfs.unlink(missing_ok=True)

    _checked_local(
        [str(udocker_bin), "create", f"--name={container_name}", repo_name],
        env=env,
        label=f"udocker create for {image}",
    )
    _checked_local(
        [str(udocker_bin), "setup", "--execmode=P2", container_name],
        env=env,
        label=f"udocker setup for {image}",
    )

    cfg = image_cfg.get("config") or {}
    metadata = {
        "image": image,
        "env": cfg.get("Env") or [],
        "working_dir": cfg.get("WorkingDir") or "",
    }
    marker.write_text(json.dumps(metadata), encoding="utf-8")
    return udocker_bin, env, container_name, metadata


def _run_on_host(script_path: str, stage: str) -> int:
    env = os.environ.copy()
    env["PATH"] = f"{RUNNER_ROOT}:{env.get('PATH', '')}"
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_CONFIG_COUNT"] = "1"
    env["GIT_CONFIG_KEY_0"] = "http.version"
    env["GIT_CONFIG_VALUE_0"] = "HTTP/1.1"
    env["GCM_INTERACTIVE"] = "Never"
    env["SSH_ASKPASS"] = "/bin/false"
    print(f"Anthares custom executor: stage={stage} host", flush=True)
    try:
        result = _run(["bash", script_path], env=env, timeout=HOST_STAGE_TIMEOUT)
    except subprocess.TimeoutExpired:
        print(
            f"Anthares custom executor: host stage timed out after {HOST_STAGE_TIMEOUT}s: {stage}",
            file=sys.stderr,
            flush=True,
        )
        return _build_failure_code()
    return result.returncode


def _run_in_container(script_path: str, image: str) -> int:
    udocker_bin, env, container_name, metadata = _prepare_container(image)
    cmd = [
        str(udocker_bin),
        "run",
        "--user=root",
        "--containerauth",
        "-v",
        f"{BUILDS_ROOT}:{BUILDS_ROOT}",
        "-v",
        f"{CACHE_ROOT}:{CACHE_ROOT}",
    ]
    for item in metadata.get("env", []):
        if isinstance(item, str) and "=" in item:
            cmd.extend(["-e", item])
    shell = "/bin/bash" if image in BASH_IMAGES else "/bin/sh"
    cmd.extend([container_name, shell, "-s"])
    print(f"Anthares custom executor: image={image} shell={shell} stage=container", flush=True)
    try:
        with open(script_path, "rb") as script:
            result = _run(cmd, env=env, stdin=script, timeout=CONTAINER_RUN_TIMEOUT)
    except subprocess.TimeoutExpired:
        print(
            f"Anthares custom executor: container stage timed out after {CONTAINER_RUN_TIMEOUT}s image={image}",
            file=sys.stderr,
            flush=True,
        )
        return _build_failure_code()
    return result.returncode


def _cleanup_job() -> None:
    try:
        root = _job_root()
    except Exception:
        return
    shutil.rmtree(root, ignore_errors=True)


def main() -> int:
    if len(sys.argv) < 3:
        print("custom executor requires script path and stage", file=sys.stderr)
        return _build_failure_code()

    script_path = sys.argv[-2]
    stage = sys.argv[-1]
    image = os.environ.get("CUSTOM_ENV_CI_JOB_IMAGE", "").strip()

    try:
        if stage == "prepare_script":
            _reset_workspace()
        in_container = stage in CONTAINER_STAGES or (
            stage.startswith("step_") and stage != "prepare_script"
        )
        rc = _run_in_container(script_path, image) if in_container and image else _run_on_host(script_path, stage)
        if stage == "cleanup_file_variables":
            _cleanup_job()
        return 0 if rc == 0 else _build_failure_code()
    except Exception as exc:
        print(f"Anthares custom executor error: {exc}", file=sys.stderr, flush=True)
        if stage == "cleanup_file_variables":
            _cleanup_job()
        return _build_failure_code()


if __name__ == "__main__":
    raise SystemExit(main())
