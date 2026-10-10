"""Collect non-secret evidence that the control plane is running remotely in GitHub Actions."""
import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def collect(env=None):
    env = env or os.environ
    if env.get("GITHUB_ACTIONS") != "true":
        raise RuntimeError("not running in GitHub Actions")
    required = ["GITHUB_RUN_ID", "GITHUB_SHA", "GITHUB_REPOSITORY", "RUNNER_OS"]
    missing = [name for name in required if not env.get(name)]
    if missing:
        raise RuntimeError("missing CI metadata: " + ",".join(missing))
    return [{
        "task": "remote_identity",
        "status": "verified",
        "source": "github-actions",
        "detail": {
            "repository": env["GITHUB_REPOSITORY"],
            "run_id": env["GITHUB_RUN_ID"],
            "sha": env["GITHUB_SHA"],
            "runner_os": env["RUNNER_OS"],
            "runner_arch": env.get("RUNNER_ARCH", "unknown"),
        },
        "observed_at": datetime.now(timezone.utc).isoformat(),
    }]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="runtime-evidence.json")
    args = parser.parse_args()
    Path(args.output).write_text(json.dumps(collect(), indent=2), encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
