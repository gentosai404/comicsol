import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from comic_sol import (  # noqa: E402
    ResumeAction,
    atomic_write_json,
    build_resume_plan,
    init_project,
    invalidate_from,
    main,
    promote_attempt,
    read_json,
    record_generation_attempt,
    record_override,
    sha256_file,
    stage_cache_key,
)


STAGES = ("planning", "storyboard", "generation", "lettering", "composition", "export")
FIXTURES = ROOT / "tests/fixtures"
FIXTURES = ROOT / "tests/fixtures"


class ResumeTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.project = init_project(
            self.root,
            "Sunlight Courier",
            b"A courier carries the last light.",
            {"mode": "short_prompt", "language": "en"},
        )
        self._complete_project()

    def tearDown(self):
        self.temporary_directory.cleanup()

    def _write_json(self, relative, data):
        path = self.project / relative
        atomic_write_json(path, data)
        return path

    def _complete_project(self):
        story = {
            "schema_version": "1.0", "title": "Sunlight Courier",
            "scenes": [{"id": "hall", "characters": ["mira"]}],
        }
        characters = {
            "schema_version": "1.0",
            "characters": [{
                "id": "mira",
                "visual_fingerprint": {"invariants": ["amber scarf", "round clasp"]},
                "reference_path": "references/characters/mira.png",
            }],
        }
        storyboard = {
            "schema_version": "1.0",
            "pages": [{
                "number": 1, "layout": "full-page",
                "panels": [{
                    "id": "p01-01", "scene_id": "hall", "characters": ["mira"],
                    "rect": {"x": 64, "y": 64, "width": 1472, "height": 2272},
                    "text": [{"id": "p01-01-t01", "content": "One last delivery."}],
                }],
            }],
        }
        self._write_json("plan/story-plan.json", story)
        self._write_json("plan/character-bible.json", characters)
        self._write_json("plan/storyboard.json", storyboard)
        (self.project / "prompts/panels/p01-01.txt").write_text("panel prompt\n", "utf-8")
        for relative, color in (
            ("references/characters/mira.png", "orange"),
            ("panels/raw/p01-01.png", "navy"),
            ("panels/clean/p01-01.png", "blue"),
            ("panels/lettered/p01-01.png", "white"),
            ("pages/page-01.png", "gray"),
        ):
            Image.new("RGB", (512, 512), color).save(self.project / relative)
        (self.project / "qa/report.md").write_text("# QA\n", "utf-8")
        (self.project / "exports/sunlight-courier.pdf").write_bytes(b"%PDF-1.4\nfixture\n")

        manifest = read_json(self.project / "project.json")
        manifest["status"] = "COMPLETE"
        manifest["panels"] = ["p01-01"]
        manifest["settings"].update({"page_count": 1, "panel_count": 1})
        manifest["artifacts"] = {
            "story_plan": self._descriptor("plan/story-plan.json"),
            "character_bible": self._descriptor("plan/character-bible.json"),
            "storyboard": self._descriptor("plan/storyboard.json"),
            "qa_report": self._descriptor("qa/report.md"),
            "pdf": self._descriptor("exports/sunlight-courier.pdf"),
        }
        atomic_write_json(self.project / "project.json", manifest)
        self._write_cache_snapshot()

    def _descriptor(self, relative):
        return {"path": relative, "sha256": sha256_file(self.project / relative)}

    def _stage_material(self, stage):
        manifest = read_json(self.project / "project.json")
        story = read_json(self.project / "plan/story-plan.json")
        characters = read_json(self.project / "plan/character-bible.json")
        storyboard = read_json(self.project / "plan/storyboard.json")
        panels = [panel for page in storyboard["pages"] for panel in page["panels"]]
        if stage == "planning":
            return [read_json(self.project / "source/request.json")], [self.project / "source/input.txt"]
        if stage == "storyboard":
            identities = [{"id": item["id"]} for item in characters["characters"]]
            return [story, identities], []
        if stage == "generation":
            visual_panels = []
            for panel in panels:
                item = deepcopy(panel)
                sfx_items = [
                    text_item
                    for text_item in item.get("text", [])
                    if text_item.get("kind") == "sfx"
                ]
                if sfx_items:
                    item["text"] = sfx_items
                else:
                    item.pop("text", None)
                visual_panels.append(item)
            files = [self.project / "prompts/panels/p01-01.txt", self.project / "references/characters/mira.png"]
            return [visual_panels, characters, manifest["capability"]], files
        if stage == "lettering":
            return [[panel["text"] for panel in panels]], [self.project / "panels/clean/p01-01.png"]
        if stage == "composition":
            geometry = [{"number": page["number"], "layout": page["layout"], "panels": [p["rect"] for p in page["panels"]]} for page in storyboard["pages"]]
            return [geometry], [self.project / "panels/lettered/p01-01.png"]
        return [{"project_id": manifest["project_id"], "settings": manifest["settings"]}], [self.project / "pages/page-01.png", self.project / "qa/report.md"]

    def _write_cache_snapshot(self):
        manifest = read_json(self.project / "project.json")
        outputs = {
            "planning": ["plan/story-plan.json", "plan/character-bible.json"],
            "storyboard": ["plan/storyboard.json"],
            "generation": ["panels/raw/p01-01.png", "panels/clean/p01-01.png"],
            "lettering": ["panels/lettered/p01-01.png"],
            "composition": ["pages/page-01.png"],
            "export": ["qa/report.md", "exports/sunlight-courier.pdf"],
        }
        stages = {}
        for stage in STAGES:
            canonical_inputs, files = self._stage_material(stage)
            stages[stage] = {
                "key": stage_cache_key(stage, canonical_inputs, files, manifest["stage_versions"][stage]),
                "artifacts": {relative: sha256_file(self.project / relative) for relative in outputs[stage]},
            }
        self._write_json("logs/stage-cache.json", {"schema_version": "1.0", "stages": stages})

    def test_cache_key_is_canonical_and_excludes_timestamps(self):
        first = stage_cache_key("planning", [{"updated_at": "one", "b": 2, "a": 1}], [], "1")
        second = stage_cache_key("planning", [{"a": 1, "b": 2, "updated_at": "two"}], [], "1")
        self.assertEqual(first, second)
        self.assertNotEqual(first, stage_cache_key("planning", [{"a": 1, "b": 3}], [], "1"))

    def test_stale_v1_lettering_cache_reruns_lettering_onward_only(self):
        canonical_inputs, files = self._stage_material("lettering")
        cache = read_json(self.project / "logs/stage-cache.json")
        cache["stages"]["lettering"]["key"] = stage_cache_key(
            "lettering", canonical_inputs, files, "1"
        )
        atomic_write_json(self.project / "logs/stage-cache.json", cache)

        manifest = read_json(self.project / "project.json")
        manifest["stage_versions"]["lettering"] = "2"
        atomic_write_json(self.project / "project.json", manifest)
        raw_before = (self.project / "panels/raw/p01-01.png").read_bytes()
        clean_before = (self.project / "panels/clean/p01-01.png").read_bytes()

        actions = build_resume_plan(self.project)

        stage_actions = [
            (action.stage, action.action)
            for action in actions
            if action.artifact == "stage"
        ]
        self.assertEqual(
            [
                ("planning", "reuse"),
                ("storyboard", "reuse"),
                ("generation", "reuse"),
                ("lettering", "rerun"),
                ("composition", "rerun"),
                ("export", "rerun"),
            ],
            stage_actions,
        )
        self.assertEqual(raw_before, (self.project / "panels/raw/p01-01.png").read_bytes())
        self.assertEqual(clean_before, (self.project / "panels/clean/p01-01.png").read_bytes())

    def test_noop_resume_does_not_write_any_file(self):
        before = {p.relative_to(self.project): (p.stat().st_mtime_ns, sha256_file(p)) for p in self.project.rglob("*") if p.is_file()}
        actions = build_resume_plan(self.project)
        after = {p.relative_to(self.project): (p.stat().st_mtime_ns, sha256_file(p)) for p in self.project.rglob("*") if p.is_file()}
        self.assertTrue(actions)
        self.assertTrue(all(action.action == "reuse" for action in actions), actions)
        self.assertEqual(before, after)

    def test_dialogue_change_invalidates_lettering_onward_only(self):
        storyboard = read_json(self.project / "plan/storyboard.json")
        storyboard["pages"][0]["panels"][0]["text"][0]["content"] = "The final delivery begins."
        atomic_write_json(self.project / "plan/storyboard.json", storyboard)
        manifest = read_json(self.project / "project.json")
        manifest["artifacts"]["storyboard"] = self._descriptor("plan/storyboard.json")
        atomic_write_json(self.project / "project.json", manifest)
        raw_hash = sha256_file(self.project / "panels/raw/p01-01.png")
        clean_hash = sha256_file(self.project / "panels/clean/p01-01.png")

        actions = build_resume_plan(self.project)

        by_stage = {action.stage: action.action for action in actions if action.artifact == "stage"}
        self.assertEqual("reuse", by_stage["generation"])
        self.assertEqual(["lettering", "composition", "export"], [stage for stage in STAGES if by_stage[stage] == "rerun"])
        self.assertEqual(raw_hash, sha256_file(self.project / "panels/raw/p01-01.png"))
        self.assertEqual(clean_hash, sha256_file(self.project / "panels/clean/p01-01.png"))

    def test_sfx_change_invalidates_generation_onward(self):
        storyboard = read_json(self.project / "plan/storyboard.json")
        storyboard["pages"][0]["panels"][0]["text"] = [{
            "id": "p01-01-sfx", "kind": "sfx", "content": "KRAK!",
        }]
        atomic_write_json(self.project / "plan/storyboard.json", storyboard)
        manifest = read_json(self.project / "project.json")
        manifest["artifacts"]["storyboard"] = self._descriptor("plan/storyboard.json")
        atomic_write_json(self.project / "project.json", manifest)
        self._write_cache_snapshot()
        baseline = build_resume_plan(self.project)
        self.assertTrue(all(action.action == "reuse" for action in baseline), baseline)
        raw_hash = sha256_file(self.project / "panels/raw/p01-01.png")
        clean_hash = sha256_file(self.project / "panels/clean/p01-01.png")

        storyboard["pages"][0]["panels"][0]["text"][0]["content"] = "BOOM!"
        atomic_write_json(self.project / "plan/storyboard.json", storyboard)
        manifest = read_json(self.project / "project.json")
        manifest["artifacts"]["storyboard"] = self._descriptor("plan/storyboard.json")
        atomic_write_json(self.project / "project.json", manifest)

        actions = build_resume_plan(self.project)

        by_stage = {action.stage: action.action for action in actions if action.artifact == "stage"}
        self.assertEqual("reuse", by_stage["storyboard"])
        self.assertEqual("regenerate", by_stage["generation"])
        self.assertTrue(all(by_stage[stage] == "rerun" for stage in ("lettering", "composition", "export")))
        self.assertEqual(raw_hash, sha256_file(self.project / "panels/raw/p01-01.png"))
        self.assertEqual(clean_hash, sha256_file(self.project / "panels/clean/p01-01.png"))

    def test_fingerprint_change_invalidates_generation_onward(self):
        characters = read_json(self.project / "plan/character-bible.json")
        characters["characters"][0]["visual_fingerprint"]["invariants"][0] = "crimson scarf"
        atomic_write_json(self.project / "plan/character-bible.json", characters)
        manifest = read_json(self.project / "project.json")
        manifest["artifacts"]["character_bible"] = self._descriptor("plan/character-bible.json")
        atomic_write_json(self.project / "project.json", manifest)

        actions = build_resume_plan(self.project)

        by_stage = {action.stage: action.action for action in actions if action.artifact == "stage"}
        self.assertEqual("reuse", by_stage["storyboard"])
        self.assertEqual("regenerate", by_stage["generation"])
        self.assertTrue(all(by_stage[stage] == "rerun" for stage in ("lettering", "composition", "export")))

    def test_missing_or_hash_mismatch_invalidates_earliest_owner(self):
        (self.project / "pages/page-01.png").unlink()
        actions = build_resume_plan(self.project)
        by_stage = {action.stage: action.action for action in actions if action.artifact == "stage"}
        self.assertEqual("rerun", by_stage["composition"])
        self.assertEqual("rerun", by_stage["export"])
        self.assertEqual("reuse", by_stage["lettering"])

        self._complete_project()
        (self.project / "plan/storyboard.json").write_text("changed", "utf-8")
        actions = build_resume_plan(self.project)
        by_stage = {action.stage: action.action for action in actions if action.artifact == "stage"}
        self.assertEqual("reuse", by_stage["planning"])
        self.assertEqual("rerun", by_stage["storyboard"])
        self.assertTrue(all(by_stage[stage] != "reuse" for stage in STAGES[2:]))

    def test_interrupted_tmp_is_reported_and_not_deleted(self):
        interrupted = self.project / "panels/raw/.p01-01.png.crash.tmp"
        interrupted.write_bytes(b"partial")
        actions = build_resume_plan(self.project)
        self.assertTrue(any(action.artifact == "panels/raw/.p01-01.png.crash.tmp" and "interrupted" in action.reason for action in actions), actions)
        self.assertEqual(b"partial", interrupted.read_bytes())

    def test_invalidate_removes_manifest_entries_but_preserves_files(self):
        storyboard_path = self.project / "plan/storyboard.json"
        before = storyboard_path.read_bytes()
        removed = invalidate_from(self.project, "storyboard")
        self.assertEqual(["storyboard", "qa_report", "pdf"], removed)
        self.assertEqual(before, storyboard_path.read_bytes())
        self.assertNotIn("storyboard", read_json(self.project / "project.json")["artifacts"])

    def test_attempt_is_retained_until_verified_promotion(self):
        attempt = self.project / "panels/raw/p01-01.attempt-2.png"
        Image.new("RGB", (640, 960), "green").save(attempt)
        counts = record_generation_attempt(self.project, "p01-01", "visual_retry", attempt)
        self.assertEqual(1, counts["visual_retries"])
        self.assertTrue(attempt.is_file())

        destination = promote_attempt(self.project, "p01-01", attempt)
        self.assertEqual(self.project / "panels/raw/p01-01.png", destination)
        self.assertTrue(attempt.is_file())
        self.assertEqual(sha256_file(attempt), sha256_file(destination))

        broken = self.project / "panels/raw/p01-01.attempt-3.png"
        broken.write_bytes(b"not an image")
        before = sha256_file(destination)
        with self.assertRaisesRegex(ValueError, "readable raster"):
            promote_attempt(self.project, "p01-01", broken)
        self.assertEqual(before, sha256_file(destination))

    def test_retry_budgets_and_transient_accounting(self):
        for number in (2, 3):
            attempt = self.project / f"panels/raw/p01-01.attempt-{number}.png"
            Image.new("RGB", (512, 512), "green").save(attempt)
            record_generation_attempt(self.project, "p01-01", "visual_retry", attempt)
        extra = self.project / "panels/raw/p01-01.attempt-4.png"
        Image.new("RGB", (512, 512), "red").save(extra)
        with self.assertRaisesRegex(ValueError, "two visual retries"):
            record_generation_attempt(self.project, "p01-01", "visual_retry", extra)

        project = init_project(self.root, "Budget", b"Story", {"mode": "short_prompt", "language": "en"})
        for number in range(8):
            attempt = project / f"panels/raw/p01-01.transient-{number + 1}.png"
            Image.new("RGB", (512, 512), "blue").save(attempt)
            counts = record_generation_attempt(project, "p01-01", "transient_repeat", attempt)
        self.assertEqual(8, counts["global_extra_calls"])
        self.assertEqual(0, counts["visual_retries"])
        ninth = project / "panels/raw/p01-01.transient-9.png"
        Image.new("RGB", (512, 512), "blue").save(ninth)
        with self.assertRaisesRegex(ValueError, "eight extra calls"):
            record_generation_attempt(project, "p01-01", "transient_repeat", ninth)

    def test_corrupt_and_safety_failures_cannot_be_overridden(self):
        record_path = self.project / "qa/panels/p01-01.json"
        base = {
            "panel_id": "p01-01", "decision": "regenerate", "retry_reason": "failed",
            "unresolved_warnings": [], "raw_path": "panels/raw/p01-01.png",
        }
        for category in ("corrupt_image", "safety_refusal"):
            record = dict(base, failure_category=category)
            atomic_write_json(record_path, record)
            with self.subTest(category=category), self.assertRaisesRegex(ValueError, "cannot be overridden"):
                record_override(self.project, "p01-01", "accept the visual defect")

        atomic_write_json(record_path, dict(base, failure_category="visual_qa"))
        record_override(self.project, "p01-01", "minor prop drift is acceptable")
        updated = read_json(record_path)
        self.assertEqual("accept_with_warnings", updated["decision"])
        self.assertIn("minor prop drift is acceptable", updated["unresolved_warnings"])

    def test_resume_cli_commands_expose_interfaces(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(0, main(["resume-plan", os.fspath(self.project), "--json"]))
        self.assertTrue(json.loads(output.getvalue()))
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(0, main(["invalidate", os.fspath(self.project), "export"]))


class ResumeFixtureIntegrationTests(unittest.TestCase):
    def test_interrupted_fixture_reuses_pass_and_regenerates_only_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            shutil.copytree(FIXTURES / "interrupted-two-page", project)
            accepted = sha256_file(project / "panels/clean/p01-01.png")
            actions = build_resume_plan(project)
            panel_actions = {a.artifact: a.action for a in actions if a.artifact.startswith("p")}
            self.assertEqual("reuse", panel_actions["p01-01"])
            self.assertEqual("regenerate", panel_actions["p01-02"])
            self.assertEqual(accepted, sha256_file(project / "panels/clean/p01-01.png"))


if __name__ == "__main__":
    unittest.main()
