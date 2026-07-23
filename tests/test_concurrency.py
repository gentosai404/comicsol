import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

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

    def test_lock_file_is_retained_with_sanitized_pid_metadata(self):
        with project_io.ProjectLock(self.project, timeout=1.0):
            metadata = (self.project / ".comic-sol.lock").read_text(encoding="ascii")
        self.assertEqual(f"{os.getpid()}\n", metadata)
        self.assertTrue((self.project / ".comic-sol.lock").is_file())


if __name__ == "__main__":
    unittest.main()
