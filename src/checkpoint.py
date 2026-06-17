"""Checkpoint / rewind for Kiba — undo an agent turn's file + conversation changes.

A checkpoint is opened at the start of each turn. As Write/Edit modify files, the
original bytes are captured (once per file per checkpoint). `rewind()` restores those
files and truncates the conversation back to the checkpoint — a safety net for
autonomous mode.
"""

from __future__ import annotations

import threading
from pathlib import Path

# Distinct sentinels — NEVER conflate "file did not exist" with "we failed to read it".
# Overloading None caused rewind() to DELETE a pre-existing file whose bytes we couldn't
# capture (permission/IO error). Only _DID_NOT_EXIST may trigger an unlink.
_DID_NOT_EXIST = object()
_CAPTURE_FAILED = object()


class CheckpointManager:
    def __init__(self) -> None:
        self._stack: list[dict] = []
        self._current: dict | None = None
        self._lock = threading.Lock()  # background subagents may capture while a turn rewinds

    def begin(self, conversation) -> None:
        """Open a new checkpoint at the start of a turn."""
        with self._lock:
            self._current = {"conv_len": len(conversation.messages), "files": {}}
            self._stack.append(self._current)

    def capture_file(self, path) -> None:
        """Record a file's original bytes before it's first modified in this checkpoint."""
        with self._lock:
            if self._current is None:
                return
            key = str(Path(path))
            if key in self._current["files"]:
                return
            p = Path(path)
            try:
                if p.is_file():
                    self._current["files"][key] = p.read_bytes()
                else:
                    self._current["files"][key] = _DID_NOT_EXIST
            except Exception:
                # File exists but couldn't be read — record that, and NEVER delete it on rewind.
                self._current["files"][key] = _CAPTURE_FAILED

    def can_rewind(self) -> bool:
        with self._lock:
            return len(self._stack) > 0

    def rewind(self, conversation) -> dict:
        """Undo the most recent checkpoint: restore captured files + truncate conversation."""
        with self._lock:
            if not self._stack:
                return {"ok": False, "restored_files": 0}
            cp = self._stack.pop()
            self._current = self._stack[-1] if self._stack else None
        restored = 0
        for key, original in cp["files"].items():
            p = Path(key)
            try:
                if original is _DID_NOT_EXIST:
                    if p.is_file():
                        p.unlink()              # file didn't exist before the turn -> remove it
                    restored += 1
                elif original is _CAPTURE_FAILED:
                    continue                    # couldn't read original -> leave the file untouched
                else:
                    p.write_bytes(original)     # restore prior contents
                    restored += 1
            except Exception:
                pass
        try:
            del conversation.messages[cp["conv_len"]:]
        except Exception:
            pass
        return {"ok": True, "restored_files": restored}
