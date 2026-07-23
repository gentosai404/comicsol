import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import project_io


CHILD_LOCK_SCRIPT = r"""
import sys
from pathlib import Path
from scripts.project_io import ProjectLock

try:
    with ProjectLock(Path(sys.argv[1]), timeout=0.2):
        pass
except TimeoutError as error:
    print(error, file=sys.stderr)
    raise SystemExit(2)
"""

CONTENDER_AT_EMPTY_FILE_SCRIPT = r"""
import sys
from pathlib import Path
from scripts.project_io import ProjectLock

original_open = Path.open
original_lock = ProjectLock._lock
paused = False

def pause():
    global paused
    if not paused:
        paused = True
        print("READY", flush=True)
        if sys.stdin.readline().strip() != "GO":
            raise RuntimeError("missing synchronization signal")

class PausedHandle:
    def __init__(self, handle):
        self.handle = handle

    def __getattr__(self, name):
        return getattr(self.handle, name)

    def tell(self):
        position = self.handle.tell()
        pause()
        return position

Path.open = lambda path, *args, **kwargs: PausedHandle(
    original_open(path, *args, **kwargs)
)
ProjectLock._lock = staticmethod(lambda handle: (pause(), original_lock(handle))[1])
try:
    with ProjectLock(Path(sys.argv[1]), timeout=0):
        pass
except TimeoutError:
    raise SystemExit(2)
"""


class ProjectLockTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.project = Path(self.temporary_directory.name) / "project"
        self.project.mkdir()

    def tearDown(self):
        self.temporary_directory.cleanup()

    def run_child(self):
        return subprocess.run(
            [sys.executable, "-c", CHILD_LOCK_SCRIPT, os.fspath(self.project)],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_child_times_out_while_parent_holds_lock(self):
        with project_io.ProjectLock(self.project, timeout=1.0):
            result = self.run_child()
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn("project is locked", result.stderr)

    def test_child_succeeds_after_parent_releases_lock(self):
        with project_io.ProjectLock(self.project, timeout=1.0):
            pass
        result = self.run_child()
        self.assertEqual(0, result.returncode, result.stderr)

    def test_contender_never_mutates_owner_metadata_before_acquiring(self):
        contender = subprocess.Popen(
            [
                sys.executable,
                "-c",
                CONTENDER_AT_EMPTY_FILE_SCRIPT,
                os.fspath(self.project),
            ],
            text=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual("READY\n", contender.stdout.readline())
        expected = f"{os.getpid()}\n".encode("ascii")
        try:
            with project_io.ProjectLock(self.project, timeout=1.0):
                contender.stdin.write("GO\n")
                contender.stdin.flush()
                self.assertEqual(2, contender.wait(timeout=5), contender.stderr.read())
                self.assertEqual(
                    expected,
                    (self.project / ".comic-sol.lock").read_bytes(),
                )
        finally:
            if contender.poll() is None:
                contender.kill()
                contender.wait()
            contender.stdin.close()
            contender.stdout.close()
            contender.stderr.close()
        self.assertEqual(expected, (self.project / ".comic-sol.lock").read_bytes())

    def test_failure_after_acquisition_unlocks_before_close(self):
        for failed_operation in ("truncate", "write", "flush"):
            with self.subTest(operation=failed_operation):
                events = []
                original = OSError(f"{failed_operation} failed")

                class Handle:
                    def seek(self, *args):
                        pass

                    def tell(self):
                        return 1

                    def truncate(self):
                        events.append("truncate")
                        if failed_operation == "truncate":
                            raise original

                    def write(self, payload):
                        events.append("write")
                        if failed_operation == "write":
                            raise original

                    def flush(self):
                        events.append("flush")
                        if failed_operation == "flush":
                            raise original

                    def close(self):
                        events.append("close")

                lock = project_io.ProjectLock(self.project, timeout=0)
                handle = Handle()
                (self.project / ".comic-sol.lock").write_bytes(b"\0")

                def fail_unlock(unused):
                    events.append("unlock")
                    raise OSError("unlock failed")

                with (
                    mock.patch.object(Path, "open", return_value=handle),
                    mock.patch.object(
                        project_io.ProjectLock,
                        "_lock",
                        side_effect=lambda unused: events.append("lock"),
                    ),
                    mock.patch.object(
                        project_io.ProjectLock,
                        "_unlock",
                        create=True,
                        side_effect=fail_unlock,
                    ),
                ):
                    with self.assertRaises(OSError) as raised:
                        lock.__enter__()
                self.assertIs(original, raised.exception)
                self.assertEqual(["unlock", "close"], events[-2:])
                self.assertIsNone(lock._handle)

    def test_lock_file_is_retained_with_sanitized_pid_metadata(self):
        with project_io.ProjectLock(self.project, timeout=1.0):
            metadata = (self.project / ".comic-sol.lock").read_text(encoding="ascii")
        self.assertEqual(f"{os.getpid()}\n", metadata)
        self.assertTrue((self.project / ".comic-sol.lock").is_file())


if __name__ == "__main__":
    unittest.main()
