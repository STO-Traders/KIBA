"""Session management with persistence."""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field

from .conversation import Conversation


@dataclass
class Session:
    """Session manager with persistence."""
    session_id: str
    provider: str
    model: str
    conversation: Conversation = field(default_factory=Conversation)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def save(self):
        """Save session to disk."""
        session_dir = Path.home() / ".kiba" / "sessions"
        session_dir.mkdir(parents=True, exist_ok=True)

        session_file = session_dir / f"{self.session_id}.json"

        session_data = {
            "session_id": self.session_id,
            "provider": self.provider,
            "model": self.model,
            "conversation": self.conversation.to_dict(),
            "created_at": self.created_at,
            "updated_at": datetime.now().isoformat()
        }

        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)

        self.updated_at = datetime.now().isoformat()

    @classmethod
    def load(cls, session_id: str) -> Optional['Session']:
        """Load session from disk."""
        session_file = Path.home() / ".kiba" / "sessions" / f"{session_id}.json"

        if not session_file.exists():
            return None

        # Return None (not raise) on any malformed/incomplete/corrupt session file —
        # both callers (CLI --resume and REPL /load) already handle None gracefully.
        try:
            with open(session_file, 'r') as f:
                data = json.load(f)

            return cls(
                session_id=data.get("session_id", session_id),
                provider=data["provider"],
                model=data["model"],
                conversation=Conversation.from_dict(data.get("conversation", {})),
                created_at=data.get("created_at", datetime.now().isoformat()),
                updated_at=data.get("updated_at",
                                    data.get("created_at", datetime.now().isoformat())),
            )
        except (KeyError, ValueError, TypeError, json.JSONDecodeError):
            return None

    @classmethod
    def create(cls, provider: str, model: str) -> 'Session':
        """Create a new session."""
        # Microsecond precision so two sessions created in the same second don't
        # collide and overwrite each other on disk. Still lexically sortable.
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        return cls(
            session_id=session_id,
            provider=provider,
            model=model
        )
