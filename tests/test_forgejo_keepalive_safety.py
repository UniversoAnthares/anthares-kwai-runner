"""Seven isolated tests for the existing Hostinger Forgejo keepalive.

The synthetic HOME, Unix socket, process and curl stub never touch Hostinger.
Run on Linux: python3 -m unittest tests/test_forgejo_keepalive_safety.py -v
"""
import fcntl
import os
import pathlib
import shutil
import socket
import subprocess
import tempfile
import time
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "tools" / "forgejo_keepalive.sh"


@unittest.skipUnless(os.name == "posix" and pathlib.Path("/proc/self/cmdline").exists(),
                     "Linux /proc + flock required")
class ForgejoKeepaliveSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = pathlib.Path(self.temp.name)
        self.home = root / "home"
        self.base = self.home / ".anthares-forgejo"
        (self.base / "bin").mkdir(parents=True)
        (self.base / "custom" / "conf").mkdir(parents=True)
        self.conf = self.base / "custom" / "conf" / "app.ini"
        self.conf.write_text("[server]\n")
        self.binary = self.base / "bin" / "forgejo"
        self.binary.write_text(
            '#!/bin/bash\ntouch "$HOME/.anthares-forgejo/healthy"\n'
            'printf "START\\n" >> "$HOME/.anthares-forgejo/starts"\nsleep 3\n'
        )
        self.binary.chmod(0o700)
        stub_dir = root / "stub"
        stub_dir.mkdir()
        fake_curl = stub_dir / "curl"
        fake_curl.write_text(
            '#!/bin/bash\n[[ -e "$HOME/.anthares-forgejo/healthy" ]]\n'
        )
        fake_curl.chmod(0o700)
        self.env = dict(os.environ, HOME=str(self.home),
                        PATH=str(stub_dir) + ":" + os.environ["PATH"])

    def tearDown(self):
        self.temp.cleanup()

    def invoke(self):
        return subprocess.run(["bash", str(SCRIPT)], env=self.env,
                              capture_output=True, text=True, timeout=12)

    def test_healthy_runtime_is_noop(self):
        (self.base / "healthy").touch()
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ALREADY_HEALTHY=PASS", result.stdout)
        self.assertFalse((self.base / "starts").exists())

    def test_stale_socket_starts_one_daemon(self):
        socket_path = self.base / "forgejo.sock"
        sock = socket.socket(socket.AF_UNIX)
        sock.bind(str(socket_path))
        sock.close()
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("RECOVERED=PASS", result.stdout)
        self.assertEqual((self.base / "starts").read_text().count("START"), 1)
        self.assertFalse(socket_path.exists())

    def test_regular_file_socket_is_never_removed(self):
        socket_path = self.base / "forgejo.sock"
        socket_path.write_text("important")
        result = self.invoke()
        self.assertEqual(result.returncode, 73, result.stderr)
        self.assertIn("UNEXPECTED_SOCKET_TYPE", result.stderr)
        self.assertEqual(socket_path.read_text(), "important")

    def test_existing_lock_contender_is_not_success(self):
        with (self.base / "keepalive.lock").open("ab") as locked:
            fcntl.flock(locked, fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                result = self.invoke()
                self.assertEqual(result.returncode, 75, result.stderr)
                self.assertIn("RECOVERY_BUSY", result.stderr)
                self.assertFalse((self.base / "starts").exists())
            finally:
                fcntl.flock(locked, fcntl.LOCK_UN)

    def test_unhealthy_existing_daemon_fails_closed(self):
        compiler = shutil.which("cc") or shutil.which("gcc")
        if not compiler:
            self.skipTest("C compiler unavailable for process argv fixture")
        root = pathlib.Path(self.temp.name)
        src = root / "fake_daemon.c"
        src.write_text("#include <unistd.h>\nint main(void){sleep(15);return 0;}\n")
        executable = root / "fake_daemon"
        subprocess.run([compiler, str(src), "-o", str(executable)],
                       capture_output=True, check=True)
        cmd = 'exec -a "$1" "$3" web --config "$2" >/dev/null'
        process = subprocess.Popen(
            ["bash", "-c", cmd, "_", str(self.binary), str(self.conf),
             str(executable)], env=self.env)
        try:
            time.sleep(0.15)
            result = self.invoke()
            self.assertEqual(result.returncode, 70, result.stderr)
            self.assertIn("RUNNING_BUT_UNHEALTHY", result.stderr)
            self.assertIsNone(process.poll())
            self.assertFalse((self.base / "starts").exists())
        finally:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)

    def test_missing_installed_binary_fails_closed(self):
        self.binary.unlink()
        result = self.invoke()
        self.assertEqual(result.returncode, 78, result.stderr)
        self.assertIn("INSTALLATION_MISSING", result.stderr)

    def test_socket_symlink_is_never_removed(self):
        socket_path = self.base / "forgejo.sock"
        socket_path.symlink_to(self.conf)
        result = self.invoke()
        self.assertEqual(result.returncode, 73, result.stderr)
        self.assertIn("UNEXPECTED_SOCKET_SYMLINK", result.stderr)
        self.assertTrue(socket_path.is_symlink())


if __name__ == "__main__":
    unittest.main(verbosity=2)
