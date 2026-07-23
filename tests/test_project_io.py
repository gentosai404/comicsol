import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.project_io import contained_project_path


class ContainedProjectPathTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.project = self.root / "project"
        self.project.mkdir()

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_rejects_absolute_traversal_and_windows_drive_paths(self):
        for bad in (
            "../outside.png", "/tmp/outside.png", "C:/outside.png",
            "C:outside.png", r"\\server\share\file.png", "//server/share/file.png",
        ):
            with self.subTest(path=bad):
                with self.assertRaisesRegex(ValueError, "relative project path"):
                    contained_project_path(self.project, bad)

    def test_nonexistent_contained_target_obeys_must_exist(self):
        expected = self.project / "panels/new.png"
        self.assertEqual(expected, contained_project_path(self.project, "panels/new.png"))
        with self.assertRaises(FileNotFoundError):
            contained_project_path(self.project, "panels/new.png", must_exist=True)

    def test_rejects_sibling_prefix_escape(self):
        sibling = self.root / "project-other"
        sibling.mkdir()
        with self.assertRaisesRegex(ValueError, "relative project path"):
            contained_project_path(self.project, "../project-other/outside.png")

    def test_rejects_symlink_to_external_file(self):
        outside = self.root / "outside.png"
        outside.write_bytes(b"outside")
        link = self.project / "linked.png"
        try:
            link.symlink_to(outside)
        except OSError as error:
            self.skipTest(f"symlink unavailable: {error}")
        with self.assertRaisesRegex(ValueError, "escapes|symlinks"):
            contained_project_path(self.project, "linked.png", must_exist=True)

    def test_rejects_internal_directory_symlink_escape(self):
        outside = self.root / "outside"
        outside.mkdir()
        link = self.project / "panels"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError as error:
            self.skipTest(f"symlink unavailable: {error}")
        with self.assertRaisesRegex(ValueError, "escapes|symlinks"):
            contained_project_path(self.project, "panels/image.png")

    @unittest.skipUnless(os.name == "nt", "Windows junction/reparse behavior requires native Windows")
    def test_rejects_windows_directory_junction_escape(self):
        outside = self.root / "outside-junction-target"
        outside.mkdir()
        junction = self.project / "junction"
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", os.fspath(junction), os.fspath(outside)],
            capture_output=True,
            text=True,
        )
        if result.returncode:
            self.skipTest(f"junction creation unavailable: {result.stderr.strip()}")
        with self.assertRaisesRegex(ValueError, "escapes|symlinks"):
            contained_project_path(self.project, "junction/image.png")

    def test_returns_resolved_contained_path(self):
        nested = self.project / "panels/image.png"
        nested.parent.mkdir()
        nested.write_bytes(b"image")
        self.assertEqual(
            nested.resolve(),
            contained_project_path(self.project, "panels/image.png", must_exist=True),
        )


if __name__ == "__main__":
    unittest.main()
