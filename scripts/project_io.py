"""Shared trust-boundary helpers for Comic Sol project input and paths."""

from __future__ import annotations

import errno
import os
import re
import tempfile
import time
from pathlib import Path, PurePosixPath
from typing import BinaryIO


MAX_SOURCE_BYTES = 200 * 1024
SOURCE_SUFFIXES = {".txt", ".md"}
_DRIVE = re.compile(r"^[A-Za-z]:")
_LOCK_RETRY_SECONDS = 0.05


class ProjectLock:
    """Cross-process advisory lock retained at ``.comic-sol.lock``."""

    def __init__(self, project_dir: Path, timeout: float = 10.0):
        self.project_dir = Path(project_dir)
        self.timeout = timeout
        self._handle: BinaryIO | None = None

    def __enter__(self) -> "ProjectLock":
        handle = (self.project_dir / ".comic-sol.lock").open("a+b")
        self._handle = handle
        try:
            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(b"\0")
                handle.flush()
            deadline = time.monotonic() + self.timeout
            while True:
                try:
                    self._lock(handle)
                    break
                except OSError as error:
                    if not self._retryable(error) or time.monotonic() >= deadline:
                        if self._retryable(error):
                            raise TimeoutError(
                                "project is locked by another process"
                            ) from error
                        raise
                    remaining = max(0.0, deadline - time.monotonic())
                    time.sleep(min(_LOCK_RETRY_SECONDS, remaining))
            handle.seek(0)
            handle.truncate()
            handle.write(f"{os.getpid()}\n".encode("ascii"))
            handle.flush()
            return self
        except BaseException:
            handle.close()
            self._handle = None
            raise

    @staticmethod
    def _lock(handle: BinaryIO) -> None:
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

    @staticmethod
    def _retryable(error: OSError) -> bool:
        return error.errno in {errno.EACCES, errno.EAGAIN, errno.EDEADLK} or getattr(
            error, "winerror", None
        ) in {33, 36}

    def __exit__(self, exc_type, exc, traceback) -> None:
        handle = self._handle
        self._handle = None
        if handle is None:
            return
        try:
            handle.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()


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


def fsync_directory(path: Path) -> None:
    """Persist directory metadata; Windows has no stdlib directory fsync."""
    if os.name == "nt":
        return
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def durable_atomic_write(path: Path, payload: bytes) -> None:
    """Atomically publish bytes and durably persist file and directory metadata."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
        fsync_directory(path.parent)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
