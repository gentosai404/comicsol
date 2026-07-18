import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from comic_sol import atomic_write_json  # noqa: E402
from compose_pages import compose_all_pages, compose_page  # noqa: E402


class CompositionTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.project = Path(self.temporary_directory.name)
        for relative in ("plan", "panels/p01-01", "panels/p01-02", "pages"):
            (self.project / relative).mkdir(parents=True, exist_ok=True)
        self.storyboard = {
            "schema_version": "1.0",
            "pages": [{
                "number": 1,
                "layout": "two-horizontal",
                "panels": [
                    {"id": "p01-01", "rect": {"x": 64, "y": 64, "width": 1472, "height": 1120}},
                    {"id": "p01-02", "rect": {"x": 64, "y": 1216, "width": 1472, "height": 1120}},
                ],
            }],
        }
        self.settings = {"page_width": 1600, "page_height": 2400, "page_count": 1}
        Image.new("RGB", (800, 800), "red").save(
            self.project / "panels/p01-01/lettered.png"
        )
        Image.new("RGB", (800, 800), "green").save(
            self.project / "panels/p01-02/lettered.png"
        )
        atomic_write_json(self.project / "plan/storyboard.json", self.storyboard)
        atomic_write_json(self.project / "project.json", {
            "settings": self.settings, "artifacts": {}, "project_id": "composition-test",
        })

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_single_page_has_exact_dimensions_and_mode(self):
        path = compose_page(self.project, 1, self.storyboard, self.settings, {})
        with Image.open(path) as page:
            self.assertEqual((1600, 2400), page.size)
            self.assertEqual("RGB", page.mode)
            self.assertEqual("PNG", page.format)

    def test_two_panels_are_pasted_at_exact_rect_centers(self):
        path = compose_page(self.project, 1, self.storyboard, self.settings, {})
        with Image.open(path) as page:
            self.assertEqual((255, 0, 0), page.getpixel((800, 624)))
            self.assertEqual((0, 128, 0), page.getpixel((800, 1776)))
            self.assertEqual((255, 255, 255), page.getpixel((32, 32)))
            self.assertEqual((255, 255, 255), page.getpixel((800, 1200)))

    def test_cover_crop_is_centered_and_preserves_aspect_ratio(self):
        source = Image.new("RGB", (1200, 600), "blue")
        for x in range(100):
            for y in range(600):
                source.putpixel((x, y), (255, 0, 255))
        source.save(self.project / "panels/p01-01/lettered.png")
        path = compose_page(self.project, 1, self.storyboard, self.settings, {})
        with Image.open(path) as page:
            self.assertEqual((0, 0, 255), page.getpixel((64, 624)))
            self.assertEqual((0, 0, 255), page.getpixel((1535, 624)))

    def test_missing_panel_names_id_and_writes_no_page(self):
        (self.project / "panels/p01-02/lettered.png").unlink()
        output = self.project / "pages/page-001.png"
        with self.assertRaisesRegex(FileNotFoundError, "p01-02"):
            compose_page(self.project, 1, self.storyboard, self.settings, {})
        self.assertFalse(output.exists())

    def test_repeated_composition_has_identical_bytes(self):
        path = compose_page(self.project, 1, self.storyboard, self.settings, {})
        first = hashlib.sha256(path.read_bytes()).hexdigest()
        path = compose_page(self.project, 1, self.storyboard, self.settings, {})
        self.assertEqual(first, hashlib.sha256(path.read_bytes()).hexdigest())

    def test_all_pages_returns_numeric_paths_and_writes_each_file(self):
        second = {
            "number": 2, "layout": "full-page",
            "panels": [{"id": "p02-01", "rect": {"x": 64, "y": 64, "width": 1472, "height": 2272}}],
        }
        self.storyboard["pages"].append(second)
        self.settings["page_count"] = 2
        (self.project / "panels/p02-01").mkdir(parents=True)
        Image.new("RGB", (512, 768), "blue").save(
            self.project / "panels/p02-01/lettered.png"
        )
        atomic_write_json(self.project / "plan/storyboard.json", self.storyboard)
        manifest = json.loads((self.project / "project.json").read_text("utf-8"))
        manifest["settings"] = self.settings
        atomic_write_json(self.project / "project.json", manifest)

        paths = compose_all_pages(self.project)

        self.assertEqual(["page-001.png", "page-002.png"], [path.name for path in paths])
        self.assertTrue(all(path.is_file() for path in paths))


if __name__ == "__main__":
    unittest.main()
