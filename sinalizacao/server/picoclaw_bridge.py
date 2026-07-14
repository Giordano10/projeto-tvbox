from __future__ import annotations

from dataclasses import dataclass, field
import re
import unicodedata
from typing import Any


def _normalize_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    ascii_text = "".join(character for character in decomposed if not unicodedata.combining(character))
    return re.sub(r"\s+", " ", ascii_text.lower()).strip()


@dataclass(frozen=True)
class Interpretation:
    acao: str
    tela: str | None = None
    midia: str | None = None
    titulo: str | None = None
    corpo: str | None = None
    confianca: float = 0.0
    requer_confirmacao: bool = False
    observacoes: list[str] = field(default_factory=list)


def _normalize_catalog(screen_catalog: dict[str, Any] | list[str]) -> dict[str, list[str]]:
    normalized_catalog: dict[str, list[str]] = {}
    if isinstance(screen_catalog, list):
        for screen_id in screen_catalog:
            normalized_catalog[str(screen_id)] = []
        return normalized_catalog

    for screen_id, data in screen_catalog.items():
        aliases: list[str] = []
        if isinstance(data, dict):
            aliases.extend(str(alias) for alias in data.get("aliases", []) if alias)
            label = data.get("label") or data.get("nome") or data.get("descricao")
            if label:
                aliases.append(str(label))
        normalized_catalog[str(screen_id)] = aliases
    return normalized_catalog


def infer_screen(text: str, screen_catalog: dict[str, Any] | list[str]) -> str | None:
    normalized = _normalize_text(text)
    aliases = _normalize_catalog(screen_catalog)

    for screen in aliases:
        candidate = _normalize_text(screen)
        if candidate in normalized:
            return screen
        for alias in aliases.get(screen, []):
            if _normalize_text(alias) in normalized:
                return screen
    return None


def infer_action(text: str, attachment_present: bool) -> str:
    normalized = _normalize_text(text)
    if any(keyword in normalized for keyword in ("autorizar", "liberar", "permitir", "conceder acesso", "dar acesso", "adicionar usuario", "adicionar usuario", "adicionar contato")):
        return "autorizar_usuario"
    if any(keyword in normalized for keyword in ("revogar", "remover acesso", "bloquear", "desautorizar", "retirar acesso", "desativar usuario")):
        return "revogar_usuario"
    if "listar autorizados" in normalized or "mostrar autorizados" in normalized:
        return "listar_autorizados"
    if any(keyword in normalized for keyword in ("limpa", "apaga", "vazio")):
        return "limpar"
    if any(keyword in normalized for keyword in ("rotacion", "rodar lista", "playlist")):
        return "rotacionar"
    if any(keyword in normalized for keyword in ("slide", "cartaz", "aviso", "crie", "gere", "gerar")):
        return "gerar_slide"
    if attachment_present:
        return "exibir"
    return "exibir"


def infer_payload(text: str, screen_catalog: dict[str, Any] | list[str], attachment_present: bool = False) -> Interpretation:
    screen = infer_screen(text, screen_catalog)
    action = infer_action(text, attachment_present)
    normalized = _normalize_text(text)
    confidence = 0.92 if screen else 0.55
    requires_confirmation = screen is None and action != "limpar"

    title = None
    body = None
    if action == "gerar_slide":
        if ":" in text:
            title, body = [part.strip() for part in text.split(":", 1)]
        else:
            body = text.strip()

    notes: list[str] = []
    if not attachment_present and action == "exibir":
        notes.append("texto interpretado como pedido de exibicao sem anexo")
    if screen is None:
        notes.append("tela nao identificada com confianca suficiente")
    if "telegram" in normalized or "whatsapp" in normalized:
        notes.append("origem presumida de mensageiro")

    return Interpretation(
        acao=action,
        tela=screen,
        midia=None,
        titulo=title,
        corpo=body,
        confianca=confidence,
        requer_confirmacao=requires_confirmation,
        observacoes=notes,
    )


def build_command(text: str, screen_catalog: dict[str, Any] | list[str], attachment_path: str | None = None) -> dict[str, Any]:
    interpretation = infer_payload(text, screen_catalog, attachment_present=bool(attachment_path))
    normalized = _normalize_text(text)

    target_user_id = None
    target_username = None
    target_name = None
    target_channel = None

    username_match = re.search(r"@([a-zA-Z0-9_\.]+)", text)
    if username_match:
        target_username = username_match.group(1)

    id_match = re.search(r"(?:id|chat[_ ]?id|user[_ ]?id)[:\s#]*([0-9]{4,})", normalized)
    if id_match:
        target_user_id = id_match.group(1)

    if "telegram" in normalized:
        target_channel = "telegram"
    elif "whatsapp" in normalized:
        target_channel = "whatsapp"

    command: dict[str, Any] = {
        "acao": interpretation.acao,
        "tela": interpretation.tela,
        "midia": attachment_path,
        "titulo": interpretation.titulo,
        "corpo": interpretation.corpo,
        "confianca": interpretation.confianca,
        "requer_confirmacao": interpretation.requer_confirmacao,
        "observacoes": interpretation.observacoes,
        "canal": target_channel,
        "alvo_user_id": target_user_id,
        "alvo_username": target_username,
        "alvo_nome": target_name,
    }
    return command
