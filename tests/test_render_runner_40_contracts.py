#!/usr/bin/env python3
"""Isolated, credential-free contract tests for the Anthares GitLab custom runner."""
import ast
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

REPO = Path(__file__).resolve().parents[1]
EXECUTOR = REPO / "infra/gitlab-runner-render/custom_executor.py"
spec = importlib.util.spec_from_file_location("anthares_custom_executor_under_test", EXECUTOR)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class RunnerContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.patches = [
            patch.object(runner, "JOBS_ROOT", self.root / "jobs"),
            patch.object(runner, "BUILDS_ROOT", self.root / "builds"),
            patch.object(runner, "CACHE_ROOT", self.root / "cache"),
            patch.object(runner, "RUNNER_ROOT", self.root / "runner"),
            patch.dict(os.environ, {"CUSTOM_ENV_CI_JOB_ID": "12345"}, clear=False),
        ]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)

    def workspace(self, **updates):
        env = {
            "CUSTOM_ENV_CI_PROJECT_DIR": str(runner.BUILDS_ROOT / "12345" / "project"),
            "CUSTOM_ENV_CI_PROJECT_PATH": "UniversoAnthares/anthares-wordpress",
            "CUSTOM_ENV_CI_JOB_TOKEN": "test-only-not-a-credential",
            "CUSTOM_ENV_CI_SERVER_HOST": "gitlab.com",
        }
        env.update(updates)
        return patch.dict(os.environ, env)

    def container(self, image="php:8.5-cli", metadata=None):
        if metadata is None:
            metadata = {"env": [], "image": image}
        return patch.object(runner, "_prepare_container", return_value=(
            self.root / "udocker", {"UDOCKER_DIR": str(self.root)}, "jobenv", metadata
        ))

    def test_01_failure_default(self):
        with patch.dict(os.environ, {"BUILD_FAILURE_EXIT_CODE": "1"}):
            self.assertEqual(runner._build_failure_code(), 1)

    def test_02_failure_custom(self):
        with patch.dict(os.environ, {"BUILD_FAILURE_EXIT_CODE": "7"}):
            self.assertEqual(runner._build_failure_code(), 7)

    def test_03_failure_invalid_fallback(self):
        with patch.dict(os.environ, {"BUILD_FAILURE_EXIT_CODE": "invalid"}):
            self.assertEqual(runner._build_failure_code(), 1)

    def test_04_job_root_isolated(self):
        self.assertEqual(runner._job_root(), self.root / "jobs" / "12345")
        self.assertTrue((self.root / "jobs" / "12345").is_dir())

    def test_05_job_root_rejects_letters(self):
        with patch.dict(os.environ, {"CUSTOM_ENV_CI_JOB_ID": "abc"}):
            with self.assertRaisesRegex(RuntimeError, "invalid CI job id"):
                runner._job_root()

    def test_06_job_root_rejects_traversal(self):
        with patch.dict(os.environ, {"CUSTOM_ENV_CI_JOB_ID": "../123"}):
            with self.assertRaisesRegex(RuntimeError, "invalid CI job id"):
                runner._job_root()

    def test_07_configure_isolated_paths(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(runner._configure_job(), 0)
        result = json.loads(out.getvalue())
        self.assertEqual(result["builds_dir"], str(runner.BUILDS_ROOT / "12345"))
        self.assertEqual(result["cache_dir"], str(runner.CACHE_ROOT / "12345"))
        self.assertIs(result["builds_dir_is_shared"], False)

    def test_08_configure_rejects_bad_job_id(self):
        with patch.dict(os.environ, {"CUSTOM_ENV_CI_JOB_ID": "oops"}):
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertNotEqual(runner._configure_job(), 0)

    def test_09_reset_without_project_is_noop(self):
        with patch.dict(os.environ, {"CUSTOM_ENV_CI_PROJECT_DIR": ""}):
            runner._reset_workspace()

    def test_10_reset_rejects_outside_root(self):
        with self.workspace(CUSTOM_ENV_CI_PROJECT_DIR=str(self.root / "outside")):
            with self.assertRaisesRegex(RuntimeError, "outside controlled"):
                runner._reset_workspace()

    def test_11_reset_rejects_build_root_itself(self):
        with self.workspace(CUSTOM_ENV_CI_PROJECT_DIR=str(runner.BUILDS_ROOT)):
            with self.assertRaisesRegex(RuntimeError, "outside controlled"):
                runner._reset_workspace()

    def test_12_reset_requires_checkout_token(self):
        with self.workspace(CUSTOM_ENV_CI_JOB_TOKEN=""):
            with self.assertRaisesRegex(RuntimeError, "checkout credentials"):
                runner._reset_workspace()

    def test_13_reset_rejects_project_traversal(self):
        with self.workspace(CUSTOM_ENV_CI_PROJECT_PATH="group/../project"):
            with self.assertRaisesRegex(RuntimeError, "invalid GitLab project path"):
                runner._reset_workspace()

    def test_14_reset_rejects_unexpected_host(self):
        with self.workspace(CUSTOM_ENV_CI_SERVER_HOST="evil.example"):
            with self.assertRaisesRegex(RuntimeError, "unexpected host"):
                runner._reset_workspace()

    def test_15_reset_initializes_origin(self):
        with self.workspace(), patch.object(runner.subprocess, "run") as run:
            runner._reset_workspace()
        self.assertEqual(run.call_count, 2)
        self.assertEqual(run.call_args_list[0].args[0][:3], ["git", "init", "-q"])
        self.assertIn("remote", run.call_args_list[1].args[0])

    def test_16_reset_encodes_token(self):
        with self.workspace(CUSTOM_ENV_CI_JOB_TOKEN="test:token@with/slash"), patch.object(runner.subprocess, "run") as run:
            runner._reset_workspace()
        url = run.call_args_list[1].args[0][-1]
        self.assertIn("test%3Atoken%40with%2Fslash", url)
        self.assertTrue(url.endswith("UniversoAnthares/anthares-wordpress.git"))

    def test_17_reset_removes_stale_checkout(self):
        target = runner.BUILDS_ROOT / "12345" / "project"
        target.mkdir(parents=True)
        (target / "stale").write_text("old")
        with self.workspace(), patch.object(runner.subprocess, "run"):
            runner._reset_workspace()
        self.assertTrue(target.is_dir())
        self.assertFalse((target / "stale").exists())

    def test_18_host_success(self):
        with patch.object(runner, "_run", return_value=Mock(returncode=0)):
            self.assertEqual(runner._run_on_host("/tmp/script", "get_sources"), 0)

    def test_19_host_propagates_failure(self):
        with patch.object(runner, "_run", return_value=Mock(returncode=17)):
            self.assertEqual(runner._run_on_host("/tmp/script", "get_sources"), 17)

    def test_20_host_timeout_fails(self):
        with patch.object(runner, "_run", side_effect=subprocess.TimeoutExpired("bash", 1)):
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertNotEqual(runner._run_on_host("/tmp/script", "get_sources"), 0)

    def test_21_host_disables_interactive_prompts(self):
        with patch.object(runner, "_run", return_value=Mock(returncode=0)) as call:
            runner._run_on_host("/tmp/script", "get_sources")
        env = call.call_args.kwargs["env"]
        self.assertEqual(env["GIT_TERMINAL_PROMPT"], "0")
        self.assertEqual(env["GCM_INTERACTIVE"], "Never")

    def test_22_host_uses_http11(self):
        with patch.object(runner, "_run", return_value=Mock(returncode=0)) as call:
            runner._run_on_host("/tmp/script", "get_sources")
        env = call.call_args.kwargs["env"]
        self.assertEqual(env["GIT_CONFIG_KEY_0"], "http.version")
        self.assertEqual(env["GIT_CONFIG_VALUE_0"], "HTTP/1.1")

    def test_23_php_container_uses_bash(self):
        script = self.root / "job.sh"
        script.write_text("exit 0\n")
        with self.container(), patch.object(runner, "_run", return_value=Mock(returncode=0)) as call:
            self.assertEqual(runner._run_in_container(str(script), "php:8.5-cli"), 0)
        self.assertIn("/bin/bash", call.call_args.args[0])

    def test_24_alpine_container_uses_sh(self):
        script = self.root / "job.sh"
        script.write_text("exit 0\n")
        with self.container("alpine:3.20"), patch.object(runner, "_run", return_value=Mock(returncode=0)) as call:
            runner._run_in_container(str(script), "alpine:3.20")
        self.assertIn("/bin/sh", call.call_args.args[0])

    def test_25_container_passes_image_environment(self):
        script = self.root / "job.sh"
        script.write_text("exit 0\n")
        with self.container(metadata={"env": ["A=1", "B=2"], "image": "php:8.5-cli"}), patch.object(runner, "_run", return_value=Mock(returncode=0)) as call:
            runner._run_in_container(str(script), "php:8.5-cli")
        cmd = call.call_args.args[0]
        self.assertIn("A=1", cmd)
        self.assertIn("B=2", cmd)

    def test_26_container_mounts_isolated_roots(self):
        script = self.root / "job.sh"
        script.write_text("exit 0\n")
        with self.container(), patch.object(runner, "_run", return_value=Mock(returncode=0)) as call:
            runner._run_in_container(str(script), "php:8.5-cli")
        cmd = call.call_args.args[0]
        self.assertIn(f"{runner.BUILDS_ROOT}:{runner.BUILDS_ROOT}", cmd)
        self.assertIn(f"{runner.CACHE_ROOT}:{runner.CACHE_ROOT}", cmd)

    def test_27_container_timeout_fails(self):
        script = self.root / "job.sh"
        script.write_text("exit 0\n")
        with self.container(), patch.object(runner, "_run", side_effect=subprocess.TimeoutExpired("udocker", 1)):
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertNotEqual(runner._run_in_container(str(script), "php:8.5-cli"), 0)

    def test_28_cleanup_removes_job_directory(self):
        target = runner._job_root()
        (target / "temp").write_text("secret")
        runner._cleanup_job()
        self.assertFalse(target.exists())

    def test_29_cleanup_invalid_id_safe(self):
        with patch.dict(os.environ, {"CUSTOM_ENV_CI_JOB_ID": "bad"}):
            runner._cleanup_job()

    def test_30_rejects_unapproved_image(self):
        with self.assertRaisesRegex(RuntimeError, "not allowlisted"):
            runner._prepare_container("malicious/image:latest")

    def test_31_cached_container_metadata(self):
        target = runner._job_root()
        (target / "prepared.json").write_text(json.dumps({"image": "php:8.5-cli", "env": ["X=1"]}))
        with patch.object(runner, "_ensure_tools", return_value=(self.root / "udocker", self.root / "crane")):
            _, env, name, metadata = runner._prepare_container("php:8.5-cli")
        self.assertEqual(name, "jobenv")
        self.assertEqual(metadata["env"], ["X=1"])
        self.assertIn("UDOCKER_DIR", env)

    def test_32_image_config_parses_json(self):
        with patch.object(runner, "_run", return_value=Mock(returncode=0, stdout='{"config":{"Env":["A=1"]}}')):
            result = runner._image_config(self.root / "crane", "php:8.5-cli")
        self.assertEqual(result["config"]["Env"], ["A=1"])

    def test_33_image_config_nonzero_raises(self):
        with patch.object(runner, "_run", return_value=Mock(returncode=1, stderr="denied")):
            with self.assertRaisesRegex(RuntimeError, "denied"):
                runner._image_config(self.root / "crane", "php:8.5-cli")

    def test_34_image_config_timeout_raises(self):
        with patch.object(runner, "_run", side_effect=subprocess.TimeoutExpired("crane", 1)):
            with self.assertRaisesRegex(RuntimeError, "metadata timed out"):
                runner._image_config(self.root / "crane", "php:8.5-cli")

    def test_35_local_command_success(self):
        with patch.object(runner, "_run", return_value=Mock(returncode=0)):
            self.assertEqual(runner._checked_local(["true"], label="test").returncode, 0)

    def test_36_local_command_failure(self):
        with patch.object(runner, "_run", return_value=Mock(returncode=2)):
            with self.assertRaisesRegex(RuntimeError, "test failed"):
                runner._checked_local(["false"], label="test")

    def test_37_local_command_timeout(self):
        with patch.object(runner, "_run", side_effect=subprocess.TimeoutExpired("false", 1)):
            with self.assertRaisesRegex(RuntimeError, "timed out"):
                runner._checked_local(["false"], label="test")

    def test_38_export_rootfs_success(self):
        target = self.root / "rootfs.tar"
        def fake_run(*args, **kwargs):
            target.write_bytes(b"archive")
            return Mock(returncode=0, stderr="")
        with patch.object(runner, "_run", side_effect=fake_run):
            runner._export_rootfs(self.root / "crane", "php:8.5-cli", target)
        self.assertEqual(target.read_bytes(), b"archive")

    def test_39_export_rootfs_retries_then_fails(self):
        target = self.root / "rootfs.tar"
        with patch.object(runner, "_run", return_value=Mock(returncode=1, stderr="export failed")) as call, patch.object(runner.time, "sleep"):
            with self.assertRaisesRegex(RuntimeError, "failed to export rootfs"):
                runner._export_rootfs(self.root / "crane", "php:8.5-cli", target)
        self.assertEqual(call.call_count, runner.IMAGE_EXPORT_ATTEMPTS)
        self.assertFalse(target.exists())

    def test_40_registration_uses_auth_token(self):
        source = (REPO / "infra/gitlab-runner-render/runner_service.py").read_text()
        tree = ast.parse(source)
        node = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == "register_command")
        namespace = {
            "DRIVER": self.root / "executor.py",
            "BUILDS": self.root / "builds",
            "CACHE": self.root / "cache",
        }
        namespace["DRIVER"].write_text("#! /usr/bin/env python3\n")
        exec(compile(ast.Module(body=[node], type_ignores=[]), "register_command", "exec"), namespace)
        cmd = namespace["register_command"](self.root / "binary", self.root / "config", "glrt-test-placeholder")
        self.assertIn("--token", cmd)
        self.assertNotIn("--registration-token", cmd)
        legacy = namespace["register_command"](self.root / "binary", self.root / "config", "legacy-test-placeholder")
        self.assertIn("--registration-token", legacy)
        self.assertIn("--access-level=ref_protected", legacy)


if __name__ == "__main__":
    unittest.main()
