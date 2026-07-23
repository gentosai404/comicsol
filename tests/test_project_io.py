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
        for bad in ("../outside.png", "/tmp/outside.png", "C:/outside.png"):
            with self.subTest(path=bad):
                with self.assertRaisesRegex(ValueError, "relative project path"):
                    contained_project_path(self.project, bad)

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
