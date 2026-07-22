from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import json
import shutil
from pathlib import Path
from typing import Any

import yaml

from .auth import (
    is_authorized_messenger_sender,
    is_gestor_messenger_sender,
    load_whitelist,
    revoke_messenger_authorization,
    save_whitelist,
    upsert_messenger_authorization,
    verify_local_login,
)
from .messenger_bridge import MessengerEvent, normalize_event, attachment_source_path
from .picoclaw_bridge import build_command
from .render import render_slide
from .store import JsonStore, load_json, save_json


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class ProjectPaths:
    root: Path

    @property
    def config_dir(self) -> Path:
        return self.root / "config"

    @property
    def state_dir(self) -> Path:
        return self.root / "state"

    @property
    def content_dir(self) -> Path:
        return self.root / "content"

    @property
    def logs_dir(self) -> Path:
        return self.root / "logs"

    @property
    def biblioteca_dir(self) -> Path:
        return self.content_dir / "biblioteca"

    @property
    def gerado_dir(self) -> Path:
        return self.content_dir / "gerado"

    @property
    def staging_dir(self) -> Path:
        return self.content_dir / "staging"

    @property
    def settings_file(self) -> Path:
        return self.config_dir / "settings.yml"

    @property
    def whitelist_file(self) -> Path:
        return self.config_dir / "whitelist.json"

    @property
    def telas_map_file(self) -> Path:
        return self.config_dir / "telas.map.json"

    @property
    def devices_file(self) -> Path:
        return self.config_dir / "dispositivos.json"

    @property
    def telas_state_file(self) -> Path:
        return self.state_dir / "telas.json"

    @property
    def messenger_state_file(self) -> Path:
        return self.state_dir / "mensagens.json"

    @property
    def authorized_users_file(self) -> Path:
        return self.state_dir / "autorizados.json"

    @property
    def device_status_file(self) -> Path:
        return self.state_dir / "dispositivos.json"

    @property
    def authorizations_log_file(self) -> Path:
        return self.logs_dir / "autorizacoes.log"

    @property
    def actions_log_file(self) -> Path:
        return self.logs_dir / "acoes.log"


class SignalizacaoService:
    def __init__(self, root: Path | None = None) -> None:
        self.paths = ProjectPaths(root or _project_root())
        self.paths.config_dir.mkdir(parents=True, exist_ok=True)
        self.paths.state_dir.mkdir(parents=True, exist_ok=True)
        self.paths.content_dir.mkdir(parents=True, exist_ok=True)
        self.paths.logs_dir.mkdir(parents=True, exist_ok=True)
        self.paths.biblioteca_dir.mkdir(parents=True, exist_ok=True)
        self.paths.gerado_dir.mkdir(parents=True, exist_ok=True)
        self.paths.staging_dir.mkdir(parents=True, exist_ok=True)

        self.settings = self._load_settings()
        self.whitelist = load_whitelist(self.paths.whitelist_file)
        self.screen_map = load_json(self.paths.telas_map_file, {})
        self.device_catalog_store = JsonStore(self.paths.devices_file)
        self.state_store = JsonStore(self.paths.telas_state_file)
        self.message_store = JsonStore(self.paths.messenger_state_file)
        self.authorized_store = JsonStore(self.paths.authorized_users_file)
        self.device_status_store = JsonStore(self.paths.device_status_file)
        self._ensure_initial_state()
        self._ensure_authorized_registry()
        self._ensure_device_catalog()
        self._ensure_device_status_registry()

    def _load_settings(self) -> dict[str, Any]:
        import os
        from dotenv import load_dotenv
        load_dotenv(self.paths.root / ".env")
        
        settings = {}
        if not self.paths.settings_file.exists():
            settings = {
                "porta": 8080,
                "modo": "local",
                "polling_segundos": 5,
                "flask_secret_key": "desenvolvimento-tvb",
                "picoclaw": {
                    "habilitado": True,
                    "bin": "/home/admin/picoclaw_agent",
                    "modelo": "antigravity",
                    "mensageiro": "telegram",
                },
            }
        else:
            with self.paths.settings_file.open("r", encoding="utf-8") as handle:
                settings = yaml.safe_load(handle) or {}

        # Override with environment variables
        if os.getenv("FLASK_SECRET_KEY"):
            settings["flask_secret_key"] = os.getenv("FLASK_SECRET_KEY")
        if os.getenv("GEMINI_API_KEY"):
            if "ai" not in settings:
                settings["ai"] = {}
            settings["ai"]["api_key"] = os.getenv("GEMINI_API_KEY")

        return settings

    def authenticate_local_user(self, username: str, password: str) -> bool:
        from .auth import verify_local_login
        return verify_local_login(self.whitelist, username, password)

    def register_local_user(self, username: str, password: str) -> bool:
        from .auth import register_local_user as do_register, save_whitelist
        success = do_register(self.whitelist, username, password)
        if success:
            save_whitelist(self.paths.whitelist_file, self.whitelist)
        return success

    def _ensure_initial_state(self) -> None:
        state = self.state_store.read({})
        if state:
            return
        initial_state = {screen: {"tipo": "vazio", "src": "", "desde": ""} for screen in self.available_screens()}
        self.state_store.write(initial_state)

    def _ensure_authorized_registry(self) -> None:
        registry = self.authorized_store.read({})
        if registry:
            return
        self.authorized_store.write({"items": []})

    def _ensure_device_catalog(self) -> None:
        catalog = self.device_catalog_store.read({})
        if catalog:
            return
        self.device_catalog_store.write(
            {
                screen_id: {
                    "screen_id": screen_id,
                    "label": screen_id,
                    "ip": "",
                    "ativo": False,
                    "device_token": "",
                    "aliases": [screen_id],
                }
                for screen_id in self.available_screens()
            }
        )

    def _ensure_device_status_registry(self) -> None:
        registry = self.device_status_store.read({})
        if registry:
            return
        self.device_status_store.write({"items": {}})

    def available_screens(self) -> list[str]:
        if self.screen_map:
            return sorted(self.screen_map.keys())
        current_state = self.state_store.read({})
        if current_state:
            return sorted(current_state.keys())
        return ["tv_saguao", "tv_sala", "tv_diretoria"]

    def get_state(self) -> dict[str, Any]:
        return self.state_store.read({})

    def get_screen_state(self, screen: str) -> dict[str, Any]:
        state = self.get_state().get(screen, {"tipo": "vazio", "src": "", "desde": ""})
        
        # Check expiration
        expira_em = state.get("expira_em")
        if expira_em and _utc_now() > expira_em:
            state["tipo"] = "playlist"
            state["src"] = ""
            state["expira_em"] = ""
            self._save_screen_state(screen, state)
            
        if state.get("tipo") == "playlist":
            media_list = self.list_media()
            if media_list:
                idx = int(datetime.now(timezone.utc).timestamp() // 10) % len(media_list)
                state = {**state, "src": media_list[idx]}
        return state

    def screen_catalog(self) -> dict[str, Any]:
        if self.screen_map:
            return self.screen_map
        return {screen: {"aliases": [screen]} for screen in self.available_screens()}

    def device_catalog(self) -> dict[str, Any]:
        return self.device_catalog_store.read({}) or {}

    def list_devices(self) -> list[dict[str, Any]]:
        catalog = self.device_catalog()
        statuses = (self.device_status_store.read({}) or {}).get("items", {})
        devices: list[dict[str, Any]] = []
        for screen_id, entry in catalog.items():
            status = statuses.get(screen_id, {})
            devices.append(
                {
                    "screen_id": screen_id,
                    "label": entry.get("label", screen_id),
                    "ip": entry.get("ip", ""),
                    "ativo": entry.get("ativo", False),
                    "aliases": entry.get("aliases", []),
                    "last_seen": status.get("last_seen", ""),
                    "last_seen_ip": status.get("last_seen_ip", ""),
                    "last_seen_ok": status.get("last_seen_ok", False),
                }
            )
        return sorted(devices, key=lambda item: item["screen_id"])

    def _device_available(self, screen_id: str) -> tuple[bool, str]:
        entry = self.device_catalog().get(screen_id)
        if not entry or not entry.get("ativo", False):
            return False, "TV nao encontrada/cadastrada"

        expected_ip = str(entry.get("ip", "")).strip()
        if not expected_ip:
            return False, "TV nao encontrada/cadastrada"

        statuses = (self.device_status_store.read({}) or {}).get("items", {})
        status = statuses.get(screen_id)
        if not status:
            return False, "TV nao encontrada/cadastrada"

        if not bool(status.get("last_seen_ok", False)):
            return False, "TV nao encontrada/cadastrada"

        last_seen_ip = str(status.get("last_seen_ip", "")).strip()
        if last_seen_ip != expected_ip:
            return False, "TV nao encontrada/cadastrada"

        last_seen = str(status.get("last_seen", "")).strip()
        if not last_seen:
            return False, "TV nao encontrada/cadastrada"

        ttl_seconds = int(self.settings.get("heartbeat_ttl_segundos", 15))
        try:
            last_seen_dt = datetime.fromisoformat(last_seen)
        except ValueError:
            return False, "TV nao encontrada/cadastrada"

        age_seconds = (datetime.now(timezone.utc) - last_seen_dt).total_seconds()
        if age_seconds > ttl_seconds:
            return False, "TV nao encontrada/cadastrada"

        return True, "ok"

    def register_device_heartbeat(self, payload: dict[str, Any], remote_ip: str | None = None) -> dict[str, Any]:
        screen_id = str(payload.get("screen_id", "")).strip()
        device_ip = str(payload.get("device_ip", "")).strip()
        device_token = str(payload.get("device_token", "")).strip()

        entry = self.device_catalog().get(screen_id)
        timestamp = _utc_now()
        if not entry or not entry.get("ativo", False):
            result = {"status": "recusado", "reason": "TV nao encontrada/cadastrada"}
            self._append_audit({"timestamp": timestamp, "origin": "heartbeat", "actor": screen_id, **result})
            return result

        expected_ip = str(entry.get("ip", "")).strip()
        expected_token = str(entry.get("device_token", "")).strip()
        if expected_ip and device_ip and expected_ip != device_ip:
            result = {"status": "recusado", "reason": "TV nao encontrada/cadastrada"}
            self._append_audit({"timestamp": timestamp, "origin": "heartbeat", "actor": screen_id, **result})
            return result
        if expected_token and device_token != expected_token:
            result = {"status": "recusado", "reason": "TV nao encontrada/cadastrada"}
            self._append_audit({"timestamp": timestamp, "origin": "heartbeat", "actor": screen_id, **result})
            return result

        registry = self.device_status_store.read({}) or {"items": {}}
        registry.setdefault("items", {})[screen_id] = {
            "screen_id": screen_id,
            "last_seen": timestamp,
            "last_seen_ip": remote_ip or device_ip or expected_ip,
            "last_seen_ok": True,
        }
        self.device_status_store.write(registry)
        return {"status": "ok", "screen_id": screen_id, "last_seen": timestamp}

    def list_media(self) -> list[str]:
        media_files: list[str] = []
        for path in self.paths.biblioteca_dir.rglob("*"):
            if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg"}:
                media_files.append(str(path.relative_to(self.paths.content_dir)).replace("\\", "/"))
        return sorted(media_files)

    def _append_audit(self, entry: dict[str, Any]) -> None:
        self.paths.actions_log_file.parent.mkdir(parents=True, exist_ok=True)
        with self.paths.actions_log_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _append_authorization_log(self, entry: dict[str, Any]) -> None:
        self.paths.authorizations_log_file.parent.mkdir(parents=True, exist_ok=True)
        with self.paths.authorizations_log_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _sync_authorized_registry(self) -> list[dict[str, Any]]:
        active_items: list[dict[str, Any]] = []
        for entry in self.whitelist.get("mensageiro", []):
            if entry.get("ativo", True) is False:
                continue
            active_items.append(
                {
                    "canal": entry.get("canal"),
                    "user_id": entry.get("user_id"),
                    "telegram_username": entry.get("telegram_username"),
                    "nome": entry.get("nome"),
                    "role": entry.get("role", "operador"),
                    "autorizado_por": entry.get("autorizado_por"),
                    "autorizado_em": entry.get("autorizado_em"),
                }
            )
        self.authorized_store.write({"items": active_items})
        return active_items

    def _resolve_library_media(self, relative_path: str) -> Path:
        candidate = (self.paths.content_dir / relative_path).resolve()
        if not candidate.is_relative_to(self.paths.biblioteca_dir.resolve()) and not candidate.is_relative_to(self.paths.gerado_dir.resolve()):
            raise ValueError("midia fora da biblioteca ou da area gerada")
        if not candidate.exists():
            raise FileNotFoundError(relative_path)
        return candidate

    def _save_screen_state(self, screen: str, screen_state: dict[str, Any]) -> None:
        current = self.state_store.read({})
        current[screen] = screen_state
        self.state_store.write(current)

    def _promote_attachment(self, attachment_path: Path, original_name: str | None = None) -> str:
        if not attachment_path.exists():
            raise FileNotFoundError(str(attachment_path))
        filename = original_name or attachment_path.name
        safe_name = Path(filename).name
        destination = self.paths.biblioteca_dir / safe_name
        shutil.copy2(attachment_path, destination)
        return str(destination.relative_to(self.paths.content_dir)).replace("\\", "/")

    def authenticate_local(self, username: str, password: str) -> bool:
        return verify_local_login(self.whitelist, username, password)

    def validate_messenger_sender(self, channel: str, sender_id: str, sender_username: str | None = None) -> bool:
        return is_authorized_messenger_sender(self.whitelist, channel, sender_id, sender_username)

    def validate_gestor_sender(self, channel: str, sender_id: str, sender_username: str | None = None) -> bool:
        return is_gestor_messenger_sender(self.whitelist, channel, sender_id, sender_username)

    def list_authorized_users(self) -> list[dict[str, Any]]:
        return self._sync_authorized_registry()

    def list_authorization_history(self) -> list[dict[str, Any]]:
        if not self.paths.authorizations_log_file.exists():
            return []
        entries: list[dict[str, Any]] = []
        with self.paths.authorizations_log_file.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                entries.append(json.loads(line))
        return entries

    def authorize_messenger_user(self, command: dict[str, Any], actor: str, origin: str) -> dict[str, Any]:
        timestamp = _utc_now()
        channel = str(command.get("canal") or origin or "telegram")
        target_user_id = command.get("alvo_user_id")
        target_username = command.get("alvo_username")
        target_name = command.get("alvo_nome")
        role = str(command.get("role") or "operador")

        if not target_user_id and not target_username:
            result = {"status": "recusado", "reason": "alvo ausente"}
            self._append_authorization_log({"timestamp": timestamp, "origin": origin, "actor": actor, **result, "acao": "autorizar_usuario"})
            return result

        entry = upsert_messenger_authorization(
            self.whitelist,
            channel=channel,
            sender_id=str(target_user_id) if target_user_id else None,
            sender_username=str(target_username) if target_username else None,
            nome=str(target_name) if target_name else None,
            role=role,
            authorized_by=actor,
            authorized_em=timestamp,
        )
        save_whitelist(self.paths.whitelist_file, self.whitelist)
        registry = self._sync_authorized_registry()
        result = {"status": "ok", "acao": "autorizar_usuario", "usuario": entry}
        self._append_authorization_log({"timestamp": timestamp, "origin": origin, "actor": actor, **result})
        return {**result, "autorizados": registry}

    def revoke_messenger_user(self, command: dict[str, Any], actor: str, origin: str) -> dict[str, Any]:
        timestamp = _utc_now()
        channel = str(command.get("canal") or origin or "telegram")
        target_user_id = command.get("alvo_user_id")
        target_username = command.get("alvo_username")

        entry = revoke_messenger_authorization(
            self.whitelist,
            channel=channel,
            sender_id=str(target_user_id) if target_user_id else None,
            sender_username=str(target_username) if target_username else None,
            revoked_em=timestamp,
            revoked_by=actor,
        )
        if not entry:
            result = {"status": "recusado", "reason": "alvo nao encontrado"}
            self._append_authorization_log({"timestamp": timestamp, "origin": origin, "actor": actor, **result, "acao": "revogar_usuario"})
            return result
        save_whitelist(self.paths.whitelist_file, self.whitelist)
        registry = self._sync_authorized_registry()
        result = {"status": "ok", "acao": "revogar_usuario", "usuario": entry}
        self._append_authorization_log({"timestamp": timestamp, "origin": origin, "actor": actor, **result})
        return {**result, "autorizados": registry}

    def apply_command(self, command: dict[str, Any], origin: str, actor: str, raw_text: str = "") -> dict[str, Any]:
        action = str(command.get("acao", "")).strip()
        screen = command.get("tela")
        timestamp = _utc_now()

        if not action:
            result = {"status": "recusado", "reason": "acao ausente"}
            self._append_audit({"timestamp": timestamp, "origin": origin, "actor": actor, "raw_text": raw_text, **result})
            return result
            
        duracao_minutos = command.get("duracao_minutos")
        expira_em = ""
        if isinstance(duracao_minutos, int) and duracao_minutos > 0:
            expira_em = (datetime.now(timezone.utc) + timedelta(minutes=duracao_minutos)).isoformat()

        if action == "limpar":
            if not screen:
                result = {"status": "recusado", "reason": "tela ausente"}
            elif screen not in self.available_screens():
                result = {"status": "recusado", "reason": "tela inexistente"}
            elif not self._device_available(str(screen))[0]:
                result = {"status": "recusado", "reason": self._device_available(str(screen))[1]}
            else:
                self._save_screen_state(screen, {"tipo": "vazio", "src": "", "desde": timestamp})
                result = {"status": "ok", "acao": action, "tela": screen}
            self._append_audit({"timestamp": timestamp, "origin": origin, "actor": actor, "raw_text": raw_text, **result})
            return result

        if action == "gerar_slide":
            title = str(command.get("titulo") or "Aviso")
            body = str(command.get("corpo") or raw_text or "")
            output_name = f"cartaz_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.png"
            output_path = self.paths.biblioteca_dir / output_name
            render_slide(title=title, body=body, output_path=output_path)
            relative = str(output_path.relative_to(self.paths.content_dir)).replace("\\", "/")
            result = {"status": "ok", "acao": action, "midia": relative}
            self._append_audit({"timestamp": timestamp, "origin": origin, "actor": actor, "raw_text": raw_text, **result})
            return result

        if action == "rotacionar":
            if not screen:
                result = {"status": "recusado", "reason": "tela ausente"}
                self._append_audit({"timestamp": timestamp, "origin": origin, "actor": actor, "raw_text": raw_text, **result})
                return result
            if not self._device_available(str(screen))[0]:
                result = {"status": "recusado", "reason": self._device_available(str(screen))[1]}
                self._append_audit({"timestamp": timestamp, "origin": origin, "actor": actor, "raw_text": raw_text, **result})
                return result
            current = self.get_screen_state(screen)
            current["tipo"] = "playlist"
            current["desde"] = timestamp
            self._save_screen_state(screen, current)
            result = {"status": "ok", "acao": action, "tela": screen}
            self._append_audit({"timestamp": timestamp, "origin": origin, "actor": actor, "raw_text": raw_text, **result})
            return result

        if action == "cadastrar_dispositivo":
            if not screen:
                result = {"status": "recusado", "reason": "nome da tv (tela) não informado"}
                self._append_audit({"timestamp": timestamp, "origin": origin, "actor": actor, "raw_text": raw_text, **result})
                return result
            ip = command.get("alvo_ip") or ""
            catalog = self.device_catalog_store.read({})
            if screen not in catalog:
                catalog[screen] = {
                    "screen_id": screen,
                    "label": screen.replace("_", " ").title(),
                    "ip": ip,
                    "ativo": False,
                    "device_token": "",
                    "aliases": [screen],
                }
            else:
                if ip: catalog[screen]["ip"] = ip
            self.device_catalog_store.write(catalog)
            
            state = self.state_store.read({})
            if screen not in state:
                state[screen] = {"tipo": "vazio", "src": "", "desde": timestamp}
                self.state_store.write(state)

            if self.screen_map is not None:
                if screen not in self.screen_map:
                    self.screen_map[screen] = {
                        "label": screen.replace("_", " ").title(),
                        "aliases": [screen, screen.replace("_", " ")]
                    }
                    save_json(self.paths.telas_map_file, self.screen_map)
            
            result = {"status": "ok", "acao": action, "tela": screen, "alvo_ip": ip, "message": f"TV {screen} cadastrada"}
            self._append_audit({"timestamp": timestamp, "origin": origin, "actor": actor, "raw_text": raw_text, **result})
            return result

        if action == "excluir_dispositivo":
            if not screen:
                result = {"status": "recusado", "reason": "nome da tv (tela) não informado"}
                self._append_audit({"timestamp": timestamp, "origin": origin, "actor": actor, "raw_text": raw_text, **result})
                return result
            
            catalog = self.device_catalog_store.read({})
            if screen in catalog:
                del catalog[screen]
                self.device_catalog_store.write(catalog)
            
            state = self.state_store.read({})
            if screen in state:
                del state[screen]
                self.state_store.write(state)

            if self.screen_map is not None and screen in self.screen_map:
                del self.screen_map[screen]
                save_json(self.paths.telas_map_file, self.screen_map)
            
            result = {"status": "ok", "acao": action, "tela": screen, "message": f"TV {screen} excluída"}
            self._append_audit({"timestamp": timestamp, "origin": origin, "actor": actor, "raw_text": raw_text, **result})
            return result

        if action == "exibir":
            media_ref = command.get("midia")
            if not screen:
                result = {"status": "recusado", "reason": "tela ausente"}
            elif screen not in self.available_screens():
                result = {"status": "recusado", "reason": "tela inexistente"}
            elif not self._device_available(str(screen))[0]:
                result = {"status": "recusado", "reason": self._device_available(str(screen))[1]}
            elif not media_ref:
                result = {"status": "recusado", "reason": "midia ausente"}
            else:
                media_path = self._resolve_library_media(str(media_ref))
                relative = str(media_path.relative_to(self.paths.content_dir)).replace("\\", "/")
                self._save_screen_state(screen, {"tipo": "imagem", "src": relative, "desde": timestamp})
                result = {"status": "ok", "acao": action, "tela": screen, "midia": relative}
            self._append_audit({"timestamp": timestamp, "origin": origin, "actor": actor, "raw_text": raw_text, **result})
            return result

        result = {"status": "recusado", "reason": f"acao desconhecida: {action}"}
        self._append_audit({"timestamp": timestamp, "origin": origin, "actor": actor, "raw_text": raw_text, **result})
        return result

    def handle_text_command(self, text: str, origin: str, actor: str, attachment_path: str | None = None) -> dict[str, Any]:
        ai_config = self.settings.get("ai", {})
        command = build_command(text, self.screen_catalog(), attachment_path=attachment_path, ai_config=ai_config)
        if command.get("acao") in {"autorizar_usuario", "revogar_usuario", "listar_autorizados"}:
            if command.get("acao") == "autorizar_usuario":
                return self.authorize_messenger_user(command, actor=actor, origin=origin)
            if command.get("acao") == "revogar_usuario":
                return self.revoke_messenger_user(command, actor=actor, origin=origin)
            return {"status": "ok", "autorizados": self.list_authorized_users(), "historico": self.list_authorization_history()}
        return self.apply_command(command, origin=origin, actor=actor, raw_text=text)

    def handle_messenger_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        event = normalize_event(payload)
        if not self.validate_messenger_sender(event.channel, event.sender_id, event.sender_username):
            return {"status": "recusado", "reason": "remetente nao autorizado"}

        attachment_path = attachment_source_path(event)
        media_ref = None
        if attachment_path is not None:
            media_ref = self._promote_attachment(attachment_path, event.attachment_name)

        ai_config = self.settings.get("ai", {})
        command = build_command(event.text, self.screen_catalog(), attachment_path=media_ref, ai_config=ai_config)

        if command.get("acao") in {"autorizar_usuario", "revogar_usuario", "listar_autorizados"}:
            if not self.validate_gestor_sender(event.channel, event.sender_id, event.sender_username):
                return {"status": "recusado", "reason": "somente o gestor pode gerenciar permissões"}
            if command.get("acao") == "autorizar_usuario":
                return self.authorize_messenger_user(command, actor=event.sender_name or event.sender_id, origin=event.channel)
            if command.get("acao") == "revogar_usuario":
                return self.revoke_messenger_user(command, actor=event.sender_name or event.sender_id, origin=event.channel)
            return {"status": "ok", "autorizados": self.list_authorized_users(), "historico": self.list_authorization_history()}

        result = self.apply_command(command, origin=event.channel, actor=event.sender_name or event.sender_id, raw_text=event.text)
        if result.get("status") == "ok" and media_ref and command.get("acao") == "exibir":
            result["midia"] = media_ref
        return result
