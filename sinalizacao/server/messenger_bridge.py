from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class MessengerEvent:
    channel: str
    sender_id: str
    sender_username: str | None
    sender_name: str
    text: str
    attachment_name: str | None = None
    attachment_path: str | None = None
    message_id: str | None = None


def normalize_event(payload: dict[str, Any]) -> MessengerEvent:
    return MessengerEvent(
        channel=str(payload.get("channel", "telegram")),
        sender_id=str(payload.get("sender_id", "")),
        sender_username=payload.get("sender_username"),
        sender_name=str(payload.get("sender_name", "")),
        text=str(payload.get("text", "")),
        attachment_name=payload.get("attachment_name"),
        attachment_path=payload.get("attachment_path"),
        message_id=payload.get("message_id"),
    )


def attachment_source_path(event: MessengerEvent) -> Path | None:
    if event.attachment_path:
        return Path(event.attachment_path)
    return None
