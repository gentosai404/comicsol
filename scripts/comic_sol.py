#!/usr/bin/env python3
"""Deterministic project lifecycle commands for Comic Sol."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import unicodedata
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from PIL import Image, ImageFont


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"
FONT_PATH_COMIC_REGULAR = ROOT / "assets/fonts/ComicNeue-Regular.ttf"
FONT_PATH_COMIC_BOLD = ROOT / "assets/fonts/ComicNeue-Bold.ttf"
FONT_PATH_FALLBACK = ROOT / "assets/fonts/NotoSans-Regular.ttf"
FONT_PATH = FONT_PATH_COMIC_REGULAR
PAGE_WIDTH = 1600
PAGE_HEIGHT = 2400
MARGIN = 64
GUTTER = 32

LINEAR_STATUSES = (
    "INIT",
    "PLANNED",
    "SCRIPTED",
    "STORYBOARDED",
    "REFERENCES_READY",
    "PANELS_READY",
    "QA_READY",
    "LETTERED",
    "COMPOSED",
    "EXPORTED",
    "COMPLETE",
)
TERMINAL_STATUSES = {"COMPLETE", "COMPLETE_WITH_WARNINGS"}
ALL_STATUSES = set(LINEAR_STATUSES) | {"BLOCKED", "COMPLETE_WITH_WARNINGS"}

RESUME_STAGES = (
    "planning",
    "storyboard",
    "generation",
    "lettering",
    "composition",
    "export",
)
STAGE_INVALIDATION_STATUS = {
    "planning": "INIT",
    "storyboard": "SCRIPTED",
    "generation": "REFERENCES_READY",
    "lettering": "QA_READY",
    "composition": "LETTERED",
    "export": "COMPOSED",
}
ARTIFACT_STAGE = {
    "story_plan": "planning",
    "character_bible": "planning",
    "storyboard": "storyboard",
    "qa_report": "export",
    "pdf": "export",
}
TIMESTAMP_KEYS = {"created_at", "updated_at", "detected_at", "completed_at", "timestamp"}
STAGE_CACHE_PATH = Path("logs/stage-cache.json")
GENERATION_COUNTERS_PATH = Path("logs/generation-counters.json")


@dataclass(frozen=True)
class ResumeAction:
    stage: str
    action: Literal["reuse", "regenerate", "rerun", "blocked"]
    artifact: str
    reason: str

PROJECT_DIRECTORIES = (
    "source",
    "plan",
    "references/characters",
    "references/scenes",
    "prompts/references",
    "prompts/panels",
    "panels/raw",
    "panels/clean",
    "panels/lettered",
    "qa/panels",
    "pages",
    "exports",
    "logs",
)

SENSITIVE_KEY = re.compile(
    r"(?:api[_-]?key|authorization|credential|password|private[_-]?key|secret|token)",
    re.IGNORECASE,
)
IDENTIFIER = re.compile(r"^[a-z][a-z0-9-]{0,47}$")
CATEGORY = re.compile(r"^[A-Za-z][A-Za-z0-9._-]{0,63}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
EVENT_DETAIL_KINDS = {
    "project_id": "identifier",
    "panel_id": "identifier",
    "scene_id": "identifier",
    "source_path": "path",
    "artifact_path": "path",
    "attempt_path": "path",
    "source_sha256": "sha256",
    "artifact_sha256": "sha256",
    "count": "count",
    "attempt": "count",
    "attempts": "count",
    "page_count": "count",
    "panel_count": "count",
    "category": "category",
    "action": "category",
    "kind": "category",
    "status": "category",
    "from": "category",
    "to": "category",
    "warning_present": "boolean",
    "reused": "boolean",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def canonical_json_bytes(value: object) -> bytes:
    """Return compact, sorted UTF-8 JSON bytes without a trailing newline."""
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def read_json(path: Path) -> dict[str, object]:
    """Read a UTF-8 JSON object."""
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return value


def atomic_write_bytes(path: Path, payload: bytes) -> None:
    """Atomically publish bytes through a flushed sibling temporary file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass


def atomic_write_json(path: Path, value: object) -> None:
    """Atomically write canonical human-readable artifact JSON."""
    payload = (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    atomic_write_bytes(path, payload)


def sha256_file(path: Path) -> str:
    """Return a lowercase SHA-256 digest for a file."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def slugify(title: str) -> str:
    """Convert a title to a portable version-1.0 project ID."""
    normalized = unicodedata.normalize("NFKD", title)
    ascii_title = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_title).strip("-")
    if not slug or not slug[0].isalpha():
        slug = f"comic-sol-{slug}" if slug else "comic-sol-project"
    return slug[:48].rstrip("-")


def layout_rects(name: str) -> list[dict[str, int]]:
    """Return fresh rectangles for one fixed version-1.0 page layout."""
    inner_width = PAGE_WIDTH - (2 * MARGIN)
    inner_height = PAGE_HEIGHT - (2 * MARGIN)
    half_width = (inner_width - GUTTER) // 2
    half_height = (inner_height - GUTTER) // 2
    third_height = (inner_height - (2 * GUTTER)) // 3
    hero_height = 1176
    support_height = inner_height - GUTTER - hero_height
    layouts = {
        "full-page": [
            {"x": MARGIN, "y": MARGIN, "width": inner_width, "height": inner_height},
        ],
        "two-horizontal": [
            {"x": MARGIN, "y": MARGIN, "width": inner_width, "height": half_height},
            {
                "x": MARGIN,
                "y": MARGIN + half_height + GUTTER,
                "width": inner_width,
                "height": half_height,
            },
        ],
        "three-horizontal": [
            {
                "x": MARGIN,
                "y": MARGIN + (index * (third_height + GUTTER)),
                "width": inner_width,
                "height": third_height,
            }
            for index in range(3)
        ],
        "hero-top-two-bottom": [
            {"x": MARGIN, "y": MARGIN, "width": inner_width, "height": hero_height},
            {
                "x": MARGIN,
                "y": MARGIN + hero_height + GUTTER,
                "width": half_width,
                "height": support_height,
            },
            {
                "x": MARGIN + half_width + GUTTER,
                "y": MARGIN + hero_height + GUTTER,
                "width": half_width,
                "height": support_height,
            },
        ],
        "two-top-hero-bottom": [
            {"x": MARGIN, "y": MARGIN, "width": half_width, "height": support_height},
            {
                "x": MARGIN + half_width + GUTTER,
                "y": MARGIN,
                "width": half_width,
                "height": support_height,
            },
            {
                "x": MARGIN,
                "y": MARGIN + support_height + GUTTER,
                "width": inner_width,
                "height": hero_height,
            },
        ],
    }
    try:
        return [rectangle.copy() for rectangle in layouts[name]]
    except KeyError as error:
        raise ValueError(f"unknown layout: {name}") from error


def rectangles_overlap(a: dict[str, int], b: dict[str, int]) -> bool:
    """Return whether two positive-area rectangles overlap."""
    return not (
        a["x"] + a["width"] <= b["x"]
        or b["x"] + b["width"] <= a["x"]
        or a["y"] + a["height"] <= b["y"]
        or b["y"] + b["height"] <= a["y"]
    )


def _allocate_project_directory(output_root: Path, base_slug: str) -> Path:
    output_root.mkdir(parents=True, exist_ok=True)
    suffix = 1
    while True:
        suffix_text = "" if suffix == 1 else f"-{suffix}"
        candidate_slug = f"{base_slug[: 48 - len(suffix_text)].rstrip('-')}{suffix_text}"
        candidate = output_root / candidate_slug
        try:
            candidate.mkdir()
        except FileExistsError:
            suffix += 1
            continue
        return candidate


def _manifest_from_template(
    project_id: str,
    title: str,
    source: bytes,
    request: dict[str, object],
) -> dict[str, object]:
    manifest = read_json(TEMPLATES / "manifest.json")
    timestamp = _utc_now()
    manifest["project_id"] = project_id
    manifest["title"] = title
    manifest["created_at"] = timestamp
    manifest["updated_at"] = timestamp
    manifest["status"] = "INIT"
    manifest_input = manifest["input"]
    if not isinstance(manifest_input, dict):
        raise ValueError("manifest template input must be an object")
    manifest_input["mode"] = request.get("mode", "short_prompt")
    manifest_input["language"] = request.get("language", "en")
    manifest_input["source_sha256"] = hashlib.sha256(source).hexdigest()
    return manifest


def init_project(
    output_root: Path,
    title: str,
    source: bytes,
    request: dict[str, object],
) -> Path:
    """Initialize an exclusive Comic Sol project without overwriting data."""
    if not isinstance(source, bytes):
        raise TypeError("source must be bytes")
    if not isinstance(request, dict):
        raise TypeError("request must be a JSON object")
    if not title.strip():
        raise ValueError("title must not be empty")

    project_dir = _allocate_project_directory(Path(output_root), slugify(title))
    for relative in PROJECT_DIRECTORIES:
        (project_dir / relative).mkdir(parents=True, exist_ok=False)

    atomic_write_bytes(project_dir / "source/input.txt", source)
    atomic_write_json(project_dir / "source/request.json", request)
    manifest = _manifest_from_template(project_dir.name, title.strip(), source, request)
    atomic_write_json(project_dir / "project.json", manifest)
    append_event(
        project_dir,
        "project.created",
        {
            "project_id": project_dir.name,
            "source_path": "source/input.txt",
            "source_sha256": manifest["input"]["source_sha256"],
        },
    )
    return project_dir


def _relative_event_path(value: object) -> str:
    if not isinstance(value, (str, Path)):
        raise ValueError("event path must be a relative project path")
    text = os.fspath(value).replace("\\", "/")
    if (
        not text
        or text.startswith("/")
        or re.match(r"^[A-Za-z]:/", text)
        or ".." in text.split("/")
    ):
        raise ValueError("event path must be a relative project path")
    return Path(text).as_posix()


def _sanitize_event_details(details: dict[str, object]) -> dict[str, object]:
    sanitized: dict[str, object] = {}
    for key, value in details.items():
        if SENSITIVE_KEY.search(key):
            continue
        kind = EVENT_DETAIL_KINDS.get(key)
        if kind is None:
            raise ValueError(f"unsupported event detail: {key}")
        if kind == "identifier":
            if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
                raise ValueError(f"invalid event identifier: {key}")
            sanitized[key] = value
        elif kind == "path":
            sanitized[key] = _relative_event_path(value)
        elif kind == "sha256":
            if not isinstance(value, str) or not SHA256.fullmatch(value):
                raise ValueError(f"invalid event SHA-256: {key}")
            sanitized[key] = value
        elif kind == "count":
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"invalid event count: {key}")
            sanitized[key] = value
        elif kind == "category":
            if not isinstance(value, str) or not CATEGORY.fullmatch(value):
                raise ValueError(f"invalid event category: {key}")
            sanitized[key] = value
        elif kind == "boolean":
            if not isinstance(value, bool):
                raise ValueError(f"invalid event boolean: {key}")
            sanitized[key] = value
    return sanitized


def append_event(
    project_dir: Path,
    event: str,
    details: dict[str, object],
) -> None:
    """Append one sanitized canonical JSON object to the project event log."""
    if not isinstance(event, str) or not CATEGORY.fullmatch(event):
        raise ValueError("event name must be a sanitized category")
    if not isinstance(details, dict):
        raise ValueError("event details must be an object")
    event_record = {
        "details": _sanitize_event_details(details),
        "event": event,
        "timestamp": _utc_now(),
    }
    event_path = Path(project_dir) / "logs/events.jsonl"
    event_path.parent.mkdir(parents=True, exist_ok=True)
    with event_path.open("ab") as handle:
        handle.write(canonical_json_bytes(event_record) + b"\n")
        handle.flush()
        os.fsync(handle.fileno())


def _allowed_transition(current: str, target: str) -> bool:
    if current not in ALL_STATUSES or target not in ALL_STATUSES:
        return False
    if current in TERMINAL_STATUSES or current == "BLOCKED":
        return False
    if target == "BLOCKED":
        return True
    if current == "EXPORTED" and target == "COMPLETE_WITH_WARNINGS":
        return True
    if current in LINEAR_STATUSES:
        index = LINEAR_STATUSES.index(current)
        return index + 1 < len(LINEAR_STATUSES) and LINEAR_STATUSES[index + 1] == target
    return False


def transition(
    project_dir: Path,
    target: str,
    warning: str | None = None,
) -> dict[str, object]:
    """Move a project by one legal state, publishing the manifest last."""
    project_dir = Path(project_dir)
    manifest_path = project_dir / "project.json"
    manifest = read_json(manifest_path)
    current = manifest.get("status")
    if not isinstance(current, str) or not _allowed_transition(current, target):
        raise ValueError(f"invalid Comic Sol transition: {current} -> {target}")

    warnings = manifest.get("warnings")
    if not isinstance(warnings, list):
        raise ValueError("manifest warnings must be an array")
    if warning and warning not in warnings:
        warnings.append(warning)
    manifest["status"] = target
    manifest["updated_at"] = _utc_now()

    append_event(
        project_dir,
        "project.transitioned",
        {"from": current, "to": target, "warning_present": warning is not None},
    )
    atomic_write_json(manifest_path, manifest)
    return manifest


def _without_timestamps(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: _without_timestamps(item)
            for key, item in value.items()
            if key not in TIMESTAMP_KEYS
        }
    if isinstance(value, list):
        return [_without_timestamps(item) for item in value]
    return value


def stage_cache_key(
    stage: str,
    canonical_inputs: list[object],
    files: list[Path],
    stage_version: str,
) -> str:
    """Hash timestamp-free semantic inputs, direct file hashes, and a stage version."""
    if stage not in RESUME_STAGES:
        raise ValueError(f"unknown resume stage: {stage}")
    if not isinstance(canonical_inputs, list) or not isinstance(files, list):
        raise TypeError("cache inputs and files must be lists")
    if not isinstance(stage_version, str) or not stage_version:
        raise ValueError("stage version must be a non-empty string")
    file_hashes = [sha256_file(Path(path)) for path in files]
    payload = {
        "files": file_hashes,
        "inputs": _without_timestamps(canonical_inputs),
        "stage": stage,
        "stage_version": stage_version,
    }
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def _storyboard_panels(storyboard: dict[str, object]) -> list[dict[str, object]]:
    panels: list[dict[str, object]] = []
    pages = storyboard.get("pages", [])
    if isinstance(pages, list):
        for page in pages:
            if isinstance(page, dict) and isinstance(page.get("panels"), list):
                panels.extend(panel for panel in page["panels"] if isinstance(panel, dict))
    return panels


def _existing_files(project_dir: Path, relatives: list[str]) -> list[Path]:
    return [project_dir / relative for relative in relatives if (project_dir / relative).is_file()]


def _resume_stage_material(
    project_dir: Path,
    stage: str,
    manifest: dict[str, object],
) -> tuple[list[object], list[Path]]:
    if stage == "planning":
        return [read_json(project_dir / "source/request.json")], [project_dir / "source/input.txt"]
    story = read_json(project_dir / "plan/story-plan.json")
    characters = read_json(project_dir / "plan/character-bible.json")
    if stage == "storyboard":
        character_items = characters.get("characters", [])
        identities = [
            {"id": item.get("id")}
            for item in character_items
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        ] if isinstance(character_items, list) else []
        return [story, identities], []
    storyboard = read_json(project_dir / "plan/storyboard.json")
    panels = _storyboard_panels(storyboard)
    panel_ids = [panel.get("id") for panel in panels if isinstance(panel.get("id"), str)]
    if stage == "generation":
        visual_panels = []
        for panel in panels:
            visual_panel = dict(panel)
            text_items = panel.get("text", [])
            sfx_items = [
                dict(text_item)
                for text_item in text_items
                if isinstance(text_item, dict) and text_item.get("kind") == "sfx"
            ] if isinstance(text_items, list) else []
            if sfx_items:
                visual_panel["text"] = sfx_items
            else:
                visual_panel.pop("text", None)
            visual_panels.append(visual_panel)
        prompt_paths = [f"prompts/panels/{panel_id}.txt" for panel_id in panel_ids]
        reference_paths: list[str] = []
        character_items = characters.get("characters", [])
        if isinstance(character_items, list):
            reference_paths = [
                item["reference_path"]
                for item in character_items
                if isinstance(item, dict) and isinstance(item.get("reference_path"), str)
            ]
        return (
            [visual_panels, characters, manifest.get("capability", {})],
            _existing_files(project_dir, prompt_paths + reference_paths),
        )
    if stage == "lettering":
        text = [panel.get("text", []) for panel in panels]
        return text and [text] or [[]], _existing_files(
            project_dir, [f"panels/clean/{panel_id}.png" for panel_id in panel_ids]
        )
    if stage == "composition":
        geometry = []
        pages = storyboard.get("pages", [])
        if isinstance(pages, list):
            for page in pages:
                if not isinstance(page, dict):
                    continue
                page_panels = page.get("panels", [])
                geometry.append({
                    "number": page.get("number"),
                    "layout": page.get("layout"),
                    "panels": [
                        panel.get("rect") for panel in page_panels if isinstance(panel, dict)
                    ] if isinstance(page_panels, list) else [],
                })
        return [geometry], _existing_files(
            project_dir, [f"panels/lettered/{panel_id}.png" for panel_id in panel_ids]
        )
    settings = manifest.get("settings", {})
    project_id = manifest.get("project_id")
    page_count = settings.get("page_count", 0) if isinstance(settings, dict) else 0
    page_paths = [f"pages/page-{number:02d}.png" for number in range(1, page_count + 1)] if isinstance(page_count, int) else []
    return (
        [{"project_id": project_id, "settings": settings}],
        _existing_files(project_dir, page_paths + ["qa/report.md"]),
    )


def _manifest_artifact_problem(
    project_dir: Path,
    manifest: dict[str, object],
) -> dict[str, str]:
    problems: dict[str, str] = {}
    artifacts = manifest.get("artifacts", {})
    if not isinstance(artifacts, dict):
        return {"planning": "manifest artifacts are invalid"}
    for name, descriptor in artifacts.items():
        stage = ARTIFACT_STAGE.get(name)
        if stage is None or not isinstance(descriptor, dict):
            continue
        relative = descriptor.get("path")
        expected_hash = descriptor.get("sha256")
        if not isinstance(relative, str) or not isinstance(expected_hash, str):
            problems.setdefault(stage, f"artifact descriptor is invalid: {name}")
            continue
        path = project_dir / relative
        if not path.is_file():
            problems.setdefault(stage, f"artifact is missing: {relative}")
        elif sha256_file(path) != expected_hash:
            problems.setdefault(stage, f"artifact hash mismatch: {relative}")
    return problems


def build_resume_plan(project_dir: Path) -> list[ResumeAction]:
    """Return a read-only deterministic reuse/repair plan for a generated project."""
    project_dir = Path(project_dir)
    manifest = read_json(project_dir / "project.json")
    cache = read_json(project_dir / STAGE_CACHE_PATH)
    cached_stages = cache.get("stages")
    if not isinstance(cached_stages, dict):
        raise ValueError("stage cache must contain a stages object")
    versions = manifest.get("stage_versions")
    if not isinstance(versions, dict):
        raise ValueError("manifest stage_versions must be an object")
    manifest_paths = {
        descriptor.get("path")
        for descriptor in manifest.get("artifacts", {}).values()
        if isinstance(descriptor, dict) and isinstance(descriptor.get("path"), str)
    } if isinstance(manifest.get("artifacts"), dict) else set()
    problems = _manifest_artifact_problem(project_dir, manifest)
    stale_from: int | None = None
    stale_reason = ""
    actions: list[ResumeAction] = []

    for index, stage in enumerate(RESUME_STAGES):
        cached = cached_stages.get(stage)
        problem = problems.get(stage)
        if not isinstance(cached, dict):
            problem = problem or "stage cache entry is missing"
        else:
            artifacts = cached.get("artifacts")
            if not isinstance(artifacts, dict):
                problem = problem or "cached artifact map is invalid"
            else:
                for relative, expected_hash in artifacts.items():
                    if relative in manifest_paths:
                        continue
                    path = project_dir / relative
                    if not path.is_file():
                        problem = problem or f"artifact is missing: {relative}"
                        break
                    if not isinstance(expected_hash, str) or sha256_file(path) != expected_hash:
                        problem = problem or f"artifact hash mismatch: {relative}"
                        break
            if problem is None:
                try:
                    canonical_inputs, files = _resume_stage_material(project_dir, stage, manifest)
                    current_key = stage_cache_key(stage, canonical_inputs, files, versions[stage])
                except (KeyError, OSError, TypeError, ValueError) as error:
                    problem = f"stage inputs are unavailable: {type(error).__name__}"
                else:
                    if cached.get("key") != current_key:
                        problem = "stage cache key changed"
        if problem is not None and stale_from is None:
            stale_from, stale_reason = index, problem
        if stale_from is None:
            actions.append(ResumeAction(stage, "reuse", "stage", "cache key and artifacts match"))
        else:
            action = "regenerate" if stage == "generation" else "rerun"
            reason = stale_reason if index == stale_from else f"depends on stale {RESUME_STAGES[stale_from]} stage"
            actions.append(ResumeAction(stage, action, "stage", reason))

    for temporary in sorted(project_dir.rglob("*.tmp")):
        if temporary.is_file():
            actions.append(ResumeAction(
                "generation",
                "rerun",
                temporary.relative_to(project_dir).as_posix(),
                "interrupted temporary file ignored and preserved",
            ))
    for record_path in sorted((project_dir / "qa/panels").glob("*.json")):
        record = read_json(record_path)
        panel_id = record.get("panel_id")
        decision = record.get("decision")
        if not isinstance(panel_id, str):
            continue
        accepted = decision in {"accept", "accept_with_warnings"}
        actions.append(ResumeAction(
            "generation",
            "reuse" if accepted else "regenerate",
            panel_id,
            "accepted QA artifact is reusable" if accepted else "panel QA requires regeneration",
        ))
    return actions


def invalidate_from(project_dir: Path, stage: str) -> list[str]:
    """Forget manifest/cache descriptors from a stage onward without deleting artifacts."""
    if stage not in RESUME_STAGES:
        raise ValueError(f"unknown resume stage: {stage}")
    project_dir = Path(project_dir)
    manifest_path = project_dir / "project.json"
    manifest = read_json(manifest_path)
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        raise ValueError("manifest artifacts must be an object")
    start = RESUME_STAGES.index(stage)
    removed: list[str] = []
    for name in ARTIFACT_STAGE:
        if name not in artifacts:
            continue
        owner = ARTIFACT_STAGE.get(name)
        if owner is not None and RESUME_STAGES.index(owner) >= start:
            removed.append(name)
            del artifacts[name]
    manifest["status"] = STAGE_INVALIDATION_STATUS[stage]
    manifest["updated_at"] = _utc_now()
    atomic_write_json(manifest_path, manifest)

    cache_path = project_dir / STAGE_CACHE_PATH
    if cache_path.is_file():
        cache = read_json(cache_path)
        cached_stages = cache.get("stages")
        if isinstance(cached_stages, dict):
            for downstream in RESUME_STAGES[start:]:
                cached_stages.pop(downstream, None)
            atomic_write_json(cache_path, cache)
    return removed


def _contained_project_path(project_dir: Path, path: Path) -> Path:
    project_root = project_dir.resolve()
    candidate = path if path.is_absolute() else project_dir / path
    resolved = candidate.resolve()
    if resolved != project_root and project_root not in resolved.parents:
        raise ValueError("path escapes the project directory")
    return resolved


def _read_generation_counters(project_dir: Path) -> dict[str, object]:
    path = project_dir / GENERATION_COUNTERS_PATH
    if path.is_file():
        return read_json(path)
    return {"global_extra_calls": 0, "panels": {}, "schema_version": "1.0"}


def record_generation_attempt(
    project_dir: Path,
    panel_id: str,
    kind: Literal["initial", "visual_retry", "transient_repeat"],
    attempt_path: Path,
) -> dict[str, int]:
    """Account for a retained image call while enforcing both retry budgets."""
    if not IDENTIFIER.fullmatch(panel_id):
        raise ValueError("invalid panel ID")
    if kind not in {"initial", "visual_retry", "transient_repeat"}:
        raise ValueError("unknown generation attempt kind")
    project_dir = Path(project_dir)
    attempt = _contained_project_path(project_dir, Path(attempt_path))
    if not attempt.is_file():
        raise ValueError("attempt path must be a retained file")
    counters = _read_generation_counters(project_dir)
    panels = counters.get("panels")
    if not isinstance(panels, dict):
        raise ValueError("generation counter panels must be an object")
    panel = panels.setdefault(panel_id, {
        "initial": 0, "transient_repeats": 0, "visual_retries": 0,
    })
    if not isinstance(panel, dict):
        raise ValueError("panel generation counters must be an object")
    global_extras = counters.get("global_extra_calls", 0)
    if not isinstance(global_extras, int):
        raise ValueError("global generation counter must be an integer")
    if kind == "visual_retry" and panel.get("visual_retries", 0) >= 2:
        raise ValueError("at most two visual retries are allowed per panel")
    if kind in {"visual_retry", "transient_repeat"} and global_extras >= 8:
        raise ValueError("at most eight extra calls are allowed per project")
    counter_name = {
        "initial": "initial",
        "visual_retry": "visual_retries",
        "transient_repeat": "transient_repeats",
    }[kind]
    panel[counter_name] = int(panel.get(counter_name, 0)) + 1
    if kind in {"visual_retry", "transient_repeat"}:
        global_extras += 1
        counters["global_extra_calls"] = global_extras
    atomic_write_json(project_dir / GENERATION_COUNTERS_PATH, counters)
    return {
        "global_extra_calls": global_extras,
        "initial": int(panel.get("initial", 0)),
        "transient_repeats": int(panel.get("transient_repeats", 0)),
        "visual_retries": int(panel.get("visual_retries", 0)),
    }


def _verify_raster(path: Path) -> None:
    try:
        with Image.open(path) as image:
            if image.format not in {"PNG", "JPEG", "WEBP"}:
                raise ValueError("attempt must be a readable raster")
            image.load()
            if image.width < 512 or image.height < 512:
                raise ValueError("attempt must be a readable raster at least 512px")
    except (OSError, SyntaxError) as error:
        raise ValueError("attempt must be a readable raster") from error


def promote_attempt(project_dir: Path, panel_id: str, attempt_path: Path) -> Path:
    """Verify and atomically copy one retained attempt into the accepted raw slot."""
    if not IDENTIFIER.fullmatch(panel_id):
        raise ValueError("invalid panel ID")
    project_dir = Path(project_dir)
    attempt = _contained_project_path(project_dir, Path(attempt_path))
    if not attempt.is_file():
        raise ValueError("attempt path must be a retained file")
    _verify_raster(attempt)
    destination = project_dir / f"panels/raw/{panel_id}.png"
    if destination.is_file() and sha256_file(destination) != sha256_file(attempt):
        number = 1
        while True:
            archive = destination.with_name(f"{panel_id}.attempt-{number}.png")
            if not archive.exists() and archive.resolve() != attempt.resolve():
                atomic_write_bytes(archive, destination.read_bytes())
                break
            number += 1
    atomic_write_bytes(destination, attempt.read_bytes())
    return destination


def record_override(project_dir: Path, panel_id: str, reason: str) -> None:
    """Accept an overridable visual QA failure with an explicit recorded warning."""
    if not IDENTIFIER.fullmatch(panel_id):
        raise ValueError("invalid panel ID")
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("override reason must not be empty")
    project_dir = Path(project_dir)
    record_path = project_dir / f"qa/panels/{panel_id}.json"
    record = read_json(record_path)
    category = record.get("failure_category")
    if category in {"corrupt", "corrupt_image", "safety", "safety_refusal"}:
        raise ValueError(f"{category} cannot be overridden")
    raw_path = record.get("raw_path")
    if not isinstance(raw_path, str):
        raise ValueError("corrupt images cannot be overridden")
    try:
        _verify_raster(_contained_project_path(project_dir, Path(raw_path)))
    except ValueError as error:
        raise ValueError("corrupt images cannot be overridden") from error
    warnings = record.get("unresolved_warnings")
    if not isinstance(warnings, list):
        raise ValueError("panel unresolved_warnings must be an array")
    normalized_reason = reason.strip()
    if normalized_reason not in warnings:
        warnings.append(normalized_reason)
    record["decision"] = "accept_with_warnings"
    record["retry_reason"] = None
    atomic_write_json(record_path, record)

    manifest_path = project_dir / "project.json"
    manifest = read_json(manifest_path)
    manifest_warnings = manifest.get("warnings")
    if not isinstance(manifest_warnings, list):
        raise ValueError("manifest warnings must be an array")
    if normalized_reason not in manifest_warnings:
        manifest_warnings.append(normalized_reason)
    manifest["status"] = "COMPLETE_WITH_WARNINGS"
    manifest["updated_at"] = _utc_now()
    atomic_write_json(manifest_path, manifest)
    append_event(project_dir, "panel.overridden", {"panel_id": panel_id, "action": "accepted"})


def doctor(output_root: Path) -> tuple[bool, list[str]]:
    """Check the deterministic local runtime without probing agent tools."""
    healthy = True
    messages: list[str] = []

    if sys.version_info[:2] == (3, 11):
        messages.append(f"PASS Python 3.11 ({sys.version.split()[0]})")
    else:
        healthy = False
        messages.append(f"FAIL Python 3.11 required; found {sys.version.split()[0]}")

    try:
        import PIL

        if PIL.__version__ == "11.3.0":
            messages.append("PASS Pillow 11.3.0")
        else:
            healthy = False
            messages.append(f"FAIL Pillow 11.3.0 required; found {PIL.__version__}")
    except Exception as error:
        healthy = False
        messages.append(f"FAIL Pillow check: {type(error).__name__}: {error}")

    font_checks = (
        ("Comic Neue Regular", FONT_PATH_COMIC_REGULAR),
        ("Comic Neue Bold", FONT_PATH_COMIC_BOLD),
        ("Noto Sans fallback", FONT_PATH_FALLBACK),
    )
    for label, path in font_checks:
        try:
            ImageFont.truetype(str(path), 42)
            messages.append(f"PASS font {label} loads at 42px")
        except Exception as error:
            healthy = False
            messages.append(f"FAIL font {label} at 42px: {type(error).__name__}: {error}")

    template_names = (
        "manifest.json",
        "character-bible.json",
        "story-plan.json",
        "storyboard.json",
        "panel-record.json",
        "qa-report.md.tmpl",
    )
    missing_templates = [name for name in template_names if not (TEMPLATES / name).is_file()]
    if missing_templates:
        healthy = False
        messages.append(f"FAIL templates missing: {', '.join(missing_templates)}")
    else:
        messages.append("PASS templates available")

    output_root = Path(output_root)
    try:
        output_root.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=output_root, prefix=".doctor-", delete=True) as handle:
            handle.write(b"ok")
            handle.flush()
            os.fsync(handle.fileno())
        messages.append(f"PASS output root writable: {output_root.resolve()}")
    except OSError as error:
        healthy = False
        messages.append(f"FAIL output root not writable: {type(error).__name__}: {error}")

    messages.append("INFO image capability: inspect in agent session")
    return healthy, messages


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="comic_sol.py")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--output-root", required=True, type=Path)
    init_parser.add_argument("--title", required=True)
    init_parser.add_argument("--source", required=True, type=Path)
    init_parser.add_argument("--request-json", required=True, type=Path)

    transition_parser = subparsers.add_parser("transition")
    transition_parser.add_argument("project_dir", type=Path)
    transition_parser.add_argument("target")
    transition_parser.add_argument("--warning")

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("project_dir", type=Path)
    status_parser.add_argument("--json", action="store_true", dest="as_json")

    doctor_parser = subparsers.add_parser("doctor")
    doctor_parser.add_argument(
        "--output-root", type=Path, default=Path("comic-sol-output")
    )

    resume_parser = subparsers.add_parser("resume-plan")
    resume_parser.add_argument("project_dir", type=Path)
    resume_parser.add_argument("--json", action="store_true", dest="as_json")

    invalidate_parser = subparsers.add_parser("invalidate")
    invalidate_parser.add_argument("project_dir", type=Path)
    invalidate_parser.add_argument("stage", choices=RESUME_STAGES)

    attempt_parser = subparsers.add_parser("record-attempt")
    attempt_parser.add_argument("project_dir", type=Path)
    attempt_parser.add_argument("panel_id")
    attempt_parser.add_argument("kind", choices=("initial", "visual_retry", "transient_repeat"))
    attempt_parser.add_argument("path", type=Path)

    promote_parser = subparsers.add_parser("promote-attempt")
    promote_parser.add_argument("project_dir", type=Path)
    promote_parser.add_argument("panel_id")
    promote_parser.add_argument("path", type=Path)

    override_parser = subparsers.add_parser("override-panel")
    override_parser.add_argument("project_dir", type=Path)
    override_parser.add_argument("panel_id")
    override_parser.add_argument("--reason", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the deterministic Comic Sol lifecycle CLI."""
    parser = _build_parser()
    arguments = parser.parse_args(argv)
    try:
        if arguments.command == "init":
            request = read_json(arguments.request_json)
            project = init_project(
                arguments.output_root,
                arguments.title,
                arguments.source.read_bytes(),
                request,
            )
            print(project.resolve())
        elif arguments.command == "transition":
            manifest = transition(
                arguments.project_dir, arguments.target, arguments.warning
            )
            print(f"{manifest['project_id']}: {manifest['status']}")
        elif arguments.command == "status":
            manifest = read_json(arguments.project_dir / "project.json")
            if arguments.as_json:
                print(
                    json.dumps(
                        manifest, ensure_ascii=False, indent=2, sort_keys=True
                    )
                )
            else:
                print(f"{manifest['project_id']}: {manifest['status']}")
        elif arguments.command == "doctor":
            healthy, messages = doctor(arguments.output_root)
            print("\n".join(messages))
            return 0 if healthy else 1
        elif arguments.command == "resume-plan":
            actions = build_resume_plan(arguments.project_dir)
            if arguments.as_json:
                print(json.dumps([asdict(action) for action in actions], ensure_ascii=False, indent=2, sort_keys=True))
            else:
                for action in actions:
                    print(f"{action.stage}: {action.action} {action.artifact} — {action.reason}")
        elif arguments.command == "invalidate":
            removed = invalidate_from(arguments.project_dir, arguments.stage)
            print("\n".join(removed) if removed else "no manifest artifacts removed")
        elif arguments.command == "record-attempt":
            counts = record_generation_attempt(
                arguments.project_dir, arguments.panel_id, arguments.kind, arguments.path
            )
            print(json.dumps(counts, sort_keys=True))
        elif arguments.command == "promote-attempt":
            print(promote_attempt(arguments.project_dir, arguments.panel_id, arguments.path))
        elif arguments.command == "override-panel":
            record_override(arguments.project_dir, arguments.panel_id, arguments.reason)
            print(f"{arguments.panel_id}: accepted with warnings")
        return 0
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR {type(error).__name__}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
