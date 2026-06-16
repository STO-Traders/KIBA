"""Checkpoint / rewind for Kiba — undo an agent turn's file + conversation changes.

A checkpoint is opened at the start of each turn. As Write/Edit modify files, the
original bytes are captured (once per file per checkpoint). `rewind()` restores those
files and truncates the conversation back to the checkpoint — a safety net for
autonomous mode.
"""

from __future__ import annotations

from pathlib import Path


class CheckpointManager:
    def __init__(self) -> None:
        self._stack: list[dict] = []
        self._current: dict | None = None

    def begin(self, conversation) -> None:
        """Open a new checkpoint at the start of a turn."""
        self._current = {"conv_len": len(conversation.messages), "files": {}}
        self._stack.append(self._current)

    def capture_file(self, path) -> None:
        """Record a file's original bytes before it's first modified in this checkpoint."""
        if self._current is None:
            return
        key = str(Path(path))
        if key in self._current["files"]:
            return
        p = Path(path)
        try:
            self._current["files"][key] = p.read_bytes() if p.is_file() else None
        except Exception:
            self._current["files"][key] = None

    def can_rewind(self) -> bool:
        return len(self._stack) > 0

    def rewind(self, conversation) -> dict:
        """Undo the most recent checkpoint: restore captured files + truncate conversation."""
        if not self._stack:
            return {"ok": False, "restored_files": 0}
        cp = self._stack.pop()
        self._current = self._stack[-1] if self._stack else None
        restored = 0
        for key, original in cp["files"].items():
            p = Path(key)
            try:
                if original is None:
                    if p.is_file():
                        p.unlink()          # file didn't exist before the turn -> remove it
                else:
                    p.write_bytes(original)  # restore prior contents
                restored += 1
            except Exception:
                pass
        try:
            del conversation.messages[cp["conv_len"]:]
        except Exception:
            pass
        return {"ok": True, "restored_files": restored}
