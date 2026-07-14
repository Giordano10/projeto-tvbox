from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ExibidorState:
    screen_id: str
    last_seen_src: str = ""
    last_seen_tipo: str = "vazio"
    last_downloaded_file: str = ""
    last_updated_at: str = ""
    last_error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "screen_id": self.screen_id,
            "last_seen_src": self.last_seen_src,
            "last_seen_tipo": self.last_seen_tipo,
            "last_downloaded_file": self.last_downloaded_file,
            "last_updated_at": self.last_updated_at,
            "last_error": self.last_error,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any], screen_id: str) -> "ExibidorState":
        return cls(
            screen_id=screen_id,
            last_seen_src=str(payload.get("last_seen_src", "")),
            last_seen_tipo=str(payload.get("last_seen_tipo", "vazio")),
            last_downloaded_file=str(payload.get("last_downloaded_file", "")),
            last_updated_at=str(payload.get("last_updated_at", "")),
            last_error=str(payload.get("last_error", "")),
        )

    def mark_download(self, src: str, downloaded_file: str) -> None:
        self.last_seen_src = src
        self.last_seen_tipo = "imagem"
        self.last_downloaded_file = downloaded_file
        self.last_updated_at = _utc_now()
        self.last_error = ""

    def mark_error(self, message: str) -> None:
        self.last_error = message
        self.last_updated_at = _utc_now()


def load_state(path: Path, screen_id: str) -> ExibidorState:
    if not path.exists():
        return ExibidorState(screen_id=screen_id)
    return ExibidorState.from_dict(json.loads(path.read_text(encoding="utf-8")), screen_id)


def save_state(path: Path, state: ExibidorState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state.to_dict(), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
