"""Fail-closed final and export-ready artifact validation tests."""

import hashlib
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

from comic_sol import (  # noqa: E402
    atomic_write_json,
    init_project,
    read_json,
    sha256_file,
)
from validate_project import (  # noqa: E402
    ProjectValidationError,
    ValidationIssue,
    require_valid_project,
    validate_project,
)

from test_validation import (  # noqa: E402
    valid_characters,
    valid_manifest,
    valid_panel_record,
    valid_story,
    valid_storyboard,
)


class FinalArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.project = init_project(
            self.root, "Final Test", b"A final test story.",
            {"mode": "short_prompt", "language": "en"},
        )
        manifest = read_json(self.project / "project.json")
        manifest.update(valid_manifest())
        manifest["input"]["source_sha256"] = sha256_file(
            self.project / "source/input.txt"
        )
        atomic_write_json(self.project / "project.json", manifest)
        atomic_write_json(
            self.project / "plan/story-plan.json", valid_story()
        )
        atomic_write_json(
            self.project / "plan/character-bible.json", valid_characters()
        )
        atomic_write_json(
            self.project / "plan/storyboard.json", valid_storyboard()
        )

    def tearDown(self):
        self.temporary_directory.cleanup()

    def _add_panel_files(self):
        (self.project / "prompts/panels/p01-01.txt").write_text(
            "panel prompt", encoding="utf-8"
        )
        Image.new("RGB", (512, 512), "white").save(
            self.project / "references/characters/mira.png"
        )
        raw = self.project / "panels/raw/p01-01.png"
        clean = self.project / "panels/clean/p01-01.png"
        Image.new("RGB", (736, 1136), (20, 30, 40)).save(raw)
        Image.new("RGB", (736, 1136), (20, 30, 40)).save(clean)
        record = valid_panel_record()
        record["raw_sha256"] = sha256_file(raw)
        atomic_write_json(self.project / "qa/panels/p01-01.json", record)

    def _add_lettered_page_qas(self):
        (self.project / "pages").mkdir(exist_ok=True)
        page_png = self.project / "pages/page-001.png"
        Image.new("RGB", (1600, 2400), (100, 150, 200)).save(page_png)
        page_hash = sha256_file(page_png)
        page_qa = self.project / "qa/pages/page-001.json"
        page_qa.parent.mkdir(parents=True, exist_ok=True)
        import json
        atomic_write_json(
            page_qa,
            {
                "page": 1,
                "page_path": "pages/page-001.png",
                "page_sha256": page_hash,
                "schema_version": "1.0",
                "status": "reviewed",
            },
        )
        lettered = self.project / "panels/lettered/p01-01.png"
        lettered.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (736, 1136), (10, 20, 30)).save(lettered)

    def test_final_fails_without_any_artifacts(self):
        """RED: an empty project must report missing final artifacts."""
        self._add_panel_files()
        issues = validate_project(self.project, "final")
        missing_paths = {issue.path for issue in issues}
        self.assertIn(
            "project.json",
            missing_paths,
            "final validation must report missing artifact descriptors",
        )
        self.assertGreaterEqual(
            len(issues), 3,
            f"empty artifacts should produce several final issues, got {len(issues)}",
        )

    def test_export_ready_excludes_report_and_pdf(self):
        """export-ready must not require report, PDF, or export cache."""
        self._add_panel_files()
        self._add_lettered_page_qas()
        manifest = read_json(self.project / "project.json")
        comp_cache = self.project / "cache/composition.json"
        comp_cache.parent.mkdir(exist_ok=True)
        import json
        comp_cache.write_text(
            json.dumps({"schema_version": "1.0", "stages": {}})
        )
        comp_hash = sha256_file(comp_cache)
        manifest["artifacts"] = {
            "character_bible": {
                "path": "plan/character-bible.json",
                "sha256": sha256_file(
                    self.project / "plan/character-bible.json"
                ),
            },
            "story_plan": {
                "path": "plan/story-plan.json",
                "sha256": sha256_file(
                    self.project / "plan/story-plan.json"
                ),
            },
            "storyboard": {
                "path": "plan/storyboard.json",
                "sha256": sha256_file(
                    self.project / "plan/storyboard.json"
                ),
            },
            "composition_cache": {
                "path": "cache/composition.json",
                "sha256": comp_hash,
            },
        }
        atomic_write_json(self.project / "project.json", manifest)
        issues = validate_project(self.project, "export-ready")
        self.assertEqual(
            [], issues,
            f"export-ready with panel QA, lettered, page-QA, "
            f"composition cache should pass, got {issues}",
        )

    def test_export_ready_reports_missing_page_qa(self):
        """export-ready must fail on missing page-QA record."""
        self._add_panel_files()
        (self.project / "pages").mkdir(exist_ok=True)
        page_png = self.project / "pages/page-001.png"
        Image.new("RGB", (1600, 2400), (0, 0, 0)).save(page_png)
        lettered = self.project / "panels/lettered/p01-01.png"
        lettered.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (736, 1136), (1, 1, 1)).save(lettered)
        manifest = read_json(self.project / "project.json")
        manifest["artifacts"] = {
            "character_bible": {
                "path": "plan/character-bible.json",
                "sha256": sha256_file(
                    self.project / "plan/character-bible.json"
                ),
            },
            "story_plan": {
                "path": "plan/story-plan.json",
                "sha256": sha256_file(
                    self.project / "plan/story-plan.json"
                ),
            },
            "storyboard": {
                "path": "plan/storyboard.json",
                "sha256": sha256_file(
                    self.project / "plan/storyboard.json"
                ),
            },
        }
        atomic_write_json(self.project / "project.json", manifest)
        (self.project / "cache").mkdir(exist_ok=True)
        import json
        (self.project / "cache/composition.json").write_text(
            json.dumps({"schema_version": "1.0", "stages": {}})
        )
        issues = validate_project(self.project, "export-ready")
        page_qa_issues = [
            i for i in issues
            if "page-001" in i.message or "qa/pages" in i.path
        ]
        self.assertTrue(
            len(page_qa_issues) > 0,
            f"missing page-QA must be reported, got {issues}",
        )


class GuardedOperationTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.project = init_project(
            self.root, "Guard Test", b"A guard test story.",
            {"mode": "short_prompt", "language": "en"},
        )
        manifest = read_json(self.project / "project.json")
        manifest.update(valid_manifest())
        manifest["input"]["source_sha256"] = sha256_file(
            self.project / "source/input.txt"
        )
        atomic_write_json(self.project / "project.json", manifest)
        atomic_write_json(
            self.project / "plan/story-plan.json", valid_story()
        )
        atomic_write_json(
            self.project / "plan/character-bible.json", valid_characters()
        )
        atomic_write_json(
            self.project / "plan/storyboard.json", valid_storyboard()
        )

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_require_valid_project_raises_on_invalid(self):
        with self.assertRaises(ProjectValidationError):
            require_valid_project(self.project, "final")

    def test_require_valid_project_returns_none_on_valid(self):
        # valid at plan stage
        self.assertIsNone(
            require_valid_project(self.project, "plan")
        )


if __name__ == "__main__":
    unittest.main()
