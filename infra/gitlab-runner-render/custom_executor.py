#!/usr/bin/env python3
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tarfile
import urllib.request

TOOLS_ROOT = pathlib.Path("/tmp/anthares-gitlab-custom-tools")
JOBS_ROOT = pathlib.Path("/tmp/anthares-gitlab-custom-jobs")
BUILDS_ROOT = pathlib.Path("/tmp/anthares-gitlab-runner/builds-custom")
CACHE_ROOT = pathlib.Path("/tmp/anthares-gitlab-runner/cache-custom")

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

BASH_IMAGES = {
    "php:8.5-cli",
    "node:22-bookworm-slim",
    "ubuntu:24.04",
}

CONTAINER_STAGES = {"build_script", "step_script", "after_script"}
HOST_STAGE_TIMEOUT = 600


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
    if tmp.exists():
        tmp.unlink()
    urllib.request.urlretrieve(url, tmp)
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
        actual = _sha256(archive)
        if actual != CRANE_SHA256:
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


def _image_config(crane_bin: pathlib.Path, image: str) -> dict:
    result = _run(
        [str(crane_bin), "config", "--platform", "linux/amd64", image],
        capture=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "failed to read image config")
    return json.loads(result.stdout)


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

    install = _run([str(udocker_bin), "install"], env=env)
    if install.returncode != 0:
        raise RuntimeError("udocker install failed")

    image_cfg = _image_config(crane_bin, image)
    rootfs = root / "rootfs.tar"
    exported = _run(
        [str(crane_bin), "export", "--platform", "linux/amd64", image, str(rootfs)]
    )
    if exported.returncode != 0:
        raise RuntimeError(f"failed to export rootfs for {image}")

    repo_name = "anthares/job:runtime"
    imported = _run(
        [str(udocker_bin), "import", "--platform=linux/amd64", str(rootfs), repo_name],
        env=env,
    )
    rootfs.unlink(missing_ok=True)
    if imported.returncode != 0:
        raise RuntimeError(f"failed to import rootfs for {image}")

    created = _run([str(udocker_bin), "create", f"--name={container_name}", repo_name], env=env)
    if created.returncode != 0:
        raise RuntimeError(f"failed to create rootless container for {image}")

    setup = _run(
        [str(udocker_bin), "setup", "--execmode=P2", container_name],
        env=env,
    )
    if setup.returncode != 0:
        raise RuntimeError(f"failed to configure PRoot P2 for {image}")

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
    env["GIT_TERMINAL_PROMPT"] = "0"
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
    with open(script_path, "rb") as script:
        result = _run(cmd, env=env, stdin=script)
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
        in_container = stage in CONTAINER_STAGES or (
            stage.startswith("step_") and stage != "prepare_script"
        )
        if in_container and image:
            rc = _run_in_container(script_path, image)
        else:
            rc = _run_on_host(script_path, stage)

        if stage == "cleanup_file_variables":
            _cleanup_job()

        if rc != 0:
            return _build_failure_code()
        return 0
    except Exception as exc:
        print(f"Anthares custom executor error: {exc}", file=sys.stderr, flush=True)
        if stage == "cleanup_file_variables":
            _cleanup_job()
        return _build_failure_code()


if __name__ == "__main__":
    raise SystemExit(main())
