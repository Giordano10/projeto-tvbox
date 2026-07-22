from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


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


# Cache temporario para anexos pendentes de destinacao (chat_id -> dict com attachment info)
_PENDING_ATTACHMENTS: dict[str, dict[str, Any]] = {}


def register_pending_attachment(sender_id: str, attachment_name: str, attachment_path: str) -> None:
    _PENDING_ATTACHMENTS[str(sender_id)] = {
        "attachment_name": attachment_name,
        "attachment_path": attachment_path,
    }


def pop_pending_attachment(sender_id: str) -> dict[str, Any] | None:
    return _PENDING_ATTACHMENTS.pop(str(sender_id), None)


def peek_pending_attachment(sender_id: str) -> dict[str, Any] | None:
    return _PENDING_ATTACHMENTS.get(str(sender_id))


def normalize_event(payload: dict[str, Any]) -> MessengerEvent:
    # Se o payload for um update puro do Telegram
    if "update_id" in payload or "message" in payload:
        return parse_telegram_update(payload)

    channel = str(payload.get("channel", "telegram"))
    sender_id = str(payload.get("sender_id", ""))
    sender_username = payload.get("sender_username")
    sender_name = str(payload.get("sender_name", ""))
    text = str(payload.get("text", ""))
    attachment_name = payload.get("attachment_name")
    attachment_path = payload.get("attachment_path")
    message_id = payload.get("message_id")

    # Se nao houver anexo direto, verificar se existe anexo pendente para esse remetente
    if not attachment_path and sender_id:
        pending = pop_pending_attachment(sender_id)
        if pending:
            attachment_name = pending.get("attachment_name")
            attachment_path = pending.get("attachment_path")

    return MessengerEvent(
        channel=channel,
        sender_id=sender_id,
        sender_username=sender_username,
        sender_name=sender_name,
        text=text,
        attachment_name=attachment_name,
        attachment_path=attachment_path,
        message_id=message_id,
    )


def parse_telegram_update(update: dict[str, Any]) -> MessengerEvent:
    message = update.get("message") or update.get("edited_message") or {}
    sender = message.get("from") or {}
    chat = message.get("chat") or {}

    sender_id = str(sender.get("id") or chat.get("id") or "")
    sender_username = sender.get("username")
    first_name = sender.get("first_name", "")
    last_name = sender.get("last_name", "")
    sender_name = f"{first_name} {last_name}".strip() or sender_username or sender_id

    text = message.get("text") or message.get("caption") or ""
    message_id = str(message.get("message_id", ""))

    attachment_name = None
    attachment_path = None

    # Tratamento de anexos no Telegram (photo ou document)
    if "photo" in message and isinstance(message["photo"], list) and len(message["photo"]) > 0:
        largest_photo = message["photo"][-1]
        file_id = largest_photo.get("file_id")
        attachment_name = f"telegram_{file_id}.jpg"
        attachment_path = str(Path("content/staging") / attachment_name)
    elif "document" in message:
        doc = message["document"]
        file_name = doc.get("file_name") or f"doc_{doc.get('file_id')}.png"
        attachment_name = file_name
        attachment_path = str(Path("content/staging") / attachment_name)

    if attachment_path and not text:
        # Se veio foto sem texto, registramos como pendente de destinacao
        register_pending_attachment(sender_id, attachment_name, attachment_path)
    elif not attachment_path and sender_id:
        # Se veio texto sem foto, resgatamos o anexo pendente anterior
        pending = pop_pending_attachment(sender_id)
        if pending:
            attachment_name = pending.get("attachment_name")
            attachment_path = pending.get("attachment_path")

    return MessengerEvent(
        channel="telegram",
        sender_id=sender_id,
        sender_username=sender_username,
        sender_name=sender_name,
        text=text,
        attachment_name=attachment_name,
        attachment_path=attachment_path,
        message_id=message_id,
    )


def attachment_source_path(event: MessengerEvent) -> Path | None:
    if event.attachment_path:
        return Path(event.attachment_path)
    return None

