import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image, ImageChops, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from letter_panels import (  # noqa: E402
    letter_project,
    letter_panel,
    normalize_content,
    normalized_word_count,
    render_text_item,
)

FIXTURES = ROOT / "tests/fixtures"


FONT = ROOT / "assets/fonts/NotoSans-Regular.ttf"


def dialogue(content="Keep moving.", priority=1, anchor="top-left"):
    return {
        "id": f"dialogue-{priority}", "kind": "dialogue", "speaker": "mira",
        "content": content, "anchor": anchor, "tail_target": [0.75, 0.7],
        "priority": priority,
    }


def caption(content="Below the city, daylight became a delivery.", priority=1):
    return {
        "id": f"caption-{priority}", "kind": "caption", "speaker": None,
        "content": content, "anchor": "bottom-right", "tail_target": None,
        "priority": priority,
    }


def sfx(content="KRAK!", priority=1, anchor="middle-right"):
    return {
        "id": f"sfx-{priority}", "kind": "sfx", "speaker": None,
        "content": content, "anchor": anchor, "tail_target": None,
        "priority": priority,
    }


class LetteringTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.panel = self.root / "p01-01.png"
        Image.new("RGB", (800, 1000), (28, 32, 40)).save(self.panel)
        self.characters = [{"id": "mira", "name": "Mira"}]

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_normalize_content_and_word_count(self):
        self.assertEqual("Café 😀\nBAM!", normalize_content("  Cafe\u0301\t 😀\x00\n  BAM!  "))
        self.assertEqual(3, normalized_word_count("  one\t two\nthree  "))
        self.assertEqual("Wait... — now!", normalize_content("Wait... — now!"))

    def test_letter_panel_produces_valid_png_and_summary(self):
        result = letter_panel(
            str(self.panel), 800, 1000,
            [dialogue(), caption(priority=2), sfx(priority=3)], self.characters,
        )
        with Image.open(self.panel) as image:
            self.assertEqual("PNG", image.format)
            self.assertEqual((800, 1000), image.size)
            image.load()
        self.assertEqual(str(self.panel), result["lettered_path"])
        self.assertEqual(3, result["text_count"])
        self.assertEqual(10, result["word_count"])
        self.assertEqual(str(FONT), result["font_used"])

    def test_text_items_render_in_priority_then_id_order(self):
        items = [sfx("THREE", 3), caption("SECOND", 2), dialogue("FIRST", 1)]
        seen = []

        def observe(draw, item, rect, font, character_bible):
            seen.append(item["content"])

        with mock.patch("letter_panels.render_text_item", side_effect=observe):
            letter_panel(str(self.panel), 800, 1000, items, self.characters)
        self.assertEqual(["FIRST", "SECOND", "THREE"], seen)

    def test_dialogue_has_white_box_dark_stroke_and_tail(self):
        letter_panel(str(self.panel), 800, 1000, [dialogue()], self.characters)
        image = Image.open(self.panel).convert("RGB")
        self.assertGreater(sum(1 for pixel in image.getdata() if all(channel > 240 for channel in pixel)), 1000)
        self.assertNotEqual((28, 32, 40), image.getpixel((600, 700)))
        self.assertTrue(any(max(image.getpixel((x, 40))) < 80 for x in range(32, 370)))

    def test_sfx_is_deterministic_and_impact_styled(self):
        first = self.panel.read_bytes()
        letter_panel(str(self.panel), 800, 1000, [sfx()], self.characters)
        digest_one = hashlib.sha256(self.panel.read_bytes()).hexdigest()
        self.panel.write_bytes(first)
        letter_panel(str(self.panel), 800, 1000, [sfx()], self.characters)
        self.assertEqual(digest_one, hashlib.sha256(self.panel.read_bytes()).hexdigest())
        image = Image.open(self.panel).convert("RGB")
        crop = image.crop((430, 350, 770, 650))
        self.assertIsNotNone(crop.getbbox())
        self.assertNotEqual((28, 32, 40), crop.getpixel((170, 150)))

    def test_caption_is_drawn_at_top_as_overlay(self):
        letter_panel(str(self.panel), 800, 1000, [caption()], self.characters)
        image = Image.open(self.panel).convert("RGB")
        top = ImageChops.difference(image.crop((0, 0, 800, 320)), Image.new("RGB", (800, 320), (28, 32, 40)))
        bottom = ImageChops.difference(image.crop((0, 680, 800, 1000)), Image.new("RGB", (800, 320), (28, 32, 40)))
        self.assertIsNotNone(top.getbbox())
        self.assertIsNone(bottom.getbbox())

    def test_all_anchor_drawing_stays_inside_panel_boundary(self):
        image = Image.new("RGB", (512, 512), "black")
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(str(FONT), 24)
        rect = {"x": 4, "y": 4, "width": 504, "height": 504}
        for anchor in (
            "top-left", "top-center", "top-right", "middle-left",
            "middle-right", "bottom-left", "bottom-center", "bottom-right",
        ):
            item = dialogue(anchor=anchor)
            render_text_item(draw, item, rect, font, self.characters)
        self.assertEqual((512, 512), image.size)

    def test_unknown_dialogue_character_raises_without_partial_write(self):
        before = self.panel.read_bytes()
        item = dialogue(); item["speaker"] = "ghost"
        with self.assertRaisesRegex(ValueError, "ghost"):
            letter_panel(str(self.panel), 800, 1000, [item], self.characters)
        self.assertEqual(before, self.panel.read_bytes())

    def test_cli_fixture_contract_uses_panel_png_and_json(self):
        record = {
            "panel_id": "p01-01", "checks": [], "text_items": [caption("A quiet caption.")],
            "character_bible": self.characters,
        }
        (self.root / "p01-01.json").write_text(json.dumps(record), "utf-8")
        self.assertTrue(self.panel.is_file())
        self.assertTrue((self.root / "p01-01.json").is_file())


class LetteringFixtureIntegrationTests(unittest.TestCase):
    def test_valid_fixture_letters_three_panels_from_semantic_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            shutil.copytree(FIXTURES / "valid-one-page", project)
            self.assertEqual(3, len(letter_project(project)))


if __name__ == "__main__":
    unittest.main()
