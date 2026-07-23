"""Shared trust-boundary helpers for Comic Sol project input and paths."""

from __future__ import annotations

import os
import re
from pathlib import Path, PurePosixPath


MAX_SOURCE_BYTES = 200 * 1024
SOURCE_SUFFIXES = {".txt", ".md"}
_DRIVE = re.compile(r"^[A-Za-z]:[/\\]")


def validate_source_bytes(source: bytes, suffix: str | None = None) -> str:
    if not isinstance(source, bytes):
        raise TypeError("source must be bytes")
    if len(source) > MAX_SOURCE_BYTES:
        raise ValueError("source must be at most 200 KiB as UTF-8 bytes")
    if suffix is not None and suffix.lower() not in SOURCE_SUFFIXES:
        raise ValueError("source file must use .txt or .md")
    try:
        return source.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("source must be valid UTF-8") from error


def contained_project_path(
    project_dir: Path,
    relative: str | Path,
    *,
    must_exist: bool = False,
) -> Path:
    text = os.fspath(relative).replace("\\", "/")
    if not text or text.startswith("/") or _DRIVE.match(text) or ".." in text.split("/"):
        raise ValueError("path must be a relative project path")
    root = Path(project_dir).resolve(strict=True)
    unresolved = root.joinpath(*PurePosixPath(text).parts)
    current = unresolved
    while current != root:
        if current.is_symlink():
            raise ValueError("project path must not contain symlinks")
        current = current.parent
    candidate = unresolved.resolve(strict=must_exist)
    if candidate != root and root not in candidate.parents:
        raise ValueError("path escapes the project directory")
    return candidate

