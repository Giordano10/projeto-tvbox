from __future__ import annotations

from pathlib import Path
from typing import Any

import json
from werkzeug.security import check_password_hash


DEFAULT_WHITELIST: dict[str, Any] = {"painel_local": [], "mensageiro": []}


def load_whitelist(path: Path) -> dict[str, Any]:
    if not path.exists():
        return DEFAULT_WHITELIST.copy()
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_whitelist(path: Path, whitelist: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(whitelist, handle, ensure_ascii=False, indent=2, sort_keys=True)


def verify_local_login(whitelist: dict[str, Any], username: str, password: str) -> bool:
    for entry in whitelist.get("painel_local", []):
        if entry.get("user") != username or entry.get("ativo", True) is False:
            continue
        stored_hash = str(entry.get("hash_senha", ""))
        if stored_hash.startswith("plain:"):
            return stored_hash.removeprefix("plain:") == password
        return check_password_hash(stored_hash, password)
    return False


def is_authorized_messenger_sender(
    whitelist: dict[str, Any],
    channel: str,
    sender_id: str,
    sender_username: str | None = None,
) -> bool:
    for entry in whitelist.get("mensageiro", []):
        if entry.get("canal") != channel:
            continue
        if entry.get("ativo", True) is False:
            continue
        if str(entry.get("user_id")) == str(sender_id):
            return True
        if sender_username and str(entry.get("telegram_username", "")).lstrip("@").lower() == sender_username.lstrip("@").lower():
            return True
    return False


def is_gestor_messenger_sender(
    whitelist: dict[str, Any],
    channel: str,
    sender_id: str,
    sender_username: str | None = None,
) -> bool:
    for entry in whitelist.get("mensageiro", []):
        if entry.get("canal") != channel:
            continue
        if entry.get("ativo", True) is False:
            continue
        if str(entry.get("role", "")).lower() != "gestor":
            continue
        if str(entry.get("user_id")) == str(sender_id):
            return True
        if sender_username and str(entry.get("telegram_username", "")).lstrip("@").lower() == sender_username.lstrip("@").lower():
            return True
    return False


def upsert_messenger_authorization(
    whitelist: dict[str, Any],
    *,
    channel: str,
    sender_id: str | None = None,
    sender_username: str | None = None,
    nome: str | None = None,
    role: str = "operador",
    authorized_by: str,
    authorized_em: str,
) -> dict[str, Any]:
    entries = whitelist.setdefault("mensageiro", [])
    normalized_username = sender_username.lstrip("@").strip().lower() if sender_username else None

    for entry in entries:
        if entry.get("canal") != channel:
            continue
        if sender_id and str(entry.get("user_id")) == str(sender_id):
            entry.update(
                {
                    "ativo": True,
                    "role": role,
                    "autorizado_por": authorized_by,
                    "autorizado_em": authorized_em,
                }
            )
            if sender_username:
                entry["telegram_username"] = normalized_username
            if nome:
                entry["nome"] = nome
            return entry
        if normalized_username and str(entry.get("telegram_username", "")).lstrip("@").lower() == normalized_username:
            entry.update(
                {
                    "ativo": True,
                    "role": role,
                    "autorizado_por": authorized_by,
                    "autorizado_em": authorized_em,
                }
            )
            if sender_id:
                entry["user_id"] = str(sender_id)
            if nome:
                entry["nome"] = nome
            return entry

    new_entry: dict[str, Any] = {
        "canal": channel,
        "user_id": str(sender_id or ""),
        "telegram_username": normalized_username,
        "nome": nome or sender_username or str(sender_id or ""),
        "role": role,
        "ativo": True,
        "autorizado_por": authorized_by,
        "autorizado_em": authorized_em,
    }
    entries.append(new_entry)
    return new_entry


def revoke_messenger_authorization(
    whitelist: dict[str, Any],
    *,
    channel: str,
    sender_id: str | None = None,
    sender_username: str | None = None,
    revoked_em: str,
    revoked_by: str,
) -> dict[str, Any] | None:
    normalized_username = sender_username.lstrip("@").strip().lower() if sender_username else None
    for entry in whitelist.get("mensageiro", []):
        if entry.get("canal") != channel:
            continue
        if sender_id and str(entry.get("user_id")) == str(sender_id):
            entry.update({"ativo": False, "revogado_em": revoked_em, "revogado_por": revoked_by})
            return entry
        if normalized_username and str(entry.get("telegram_username", "")).lstrip("@").lower() == normalized_username:
            entry.update({"ativo": False, "revogado_em": revoked_em, "revogado_por": revoked_by})
            return entry
    return None
