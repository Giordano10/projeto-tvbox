from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone
import tempfile
import unittest

from sinalizacao.server.service import SignalizacaoService


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _device_status_payload() -> str:
    return json.dumps(
        {
            "items": {
                "tv_saguao": {
                    "screen_id": "tv_saguao",
                    "last_seen": _utc_now(),
                    "last_seen_ip": "192.168.15.16",
                    "last_seen_ok": True,
                }
            }
        },
        ensure_ascii=False,
    )


class SignalizacaoServiceTests(unittest.TestCase):
    def test_handle_text_command_generates_slide(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for relative in ["config", "state", "content/biblioteca", "content/gerado", "logs"]:
                (root / relative).mkdir(parents=True, exist_ok=True)

            (root / "config/settings.yml").write_text(
                "porta: 8080\nmodo: local\npolling_segundos: 5\nflask_secret_key: teste\npicoclaw:\n  habilitado: true\n  bin: /home/admin/picoclaw_agent\n  modelo: antigravity\n  mensageiro: telegram\n",
                encoding="utf-8",
            )
            (root / "config/whitelist.json").write_text(
                '{"painel_local": [{"user": "diretor", "hash_senha": "plain:trocar123", "role": "gestor", "ativo": true}], "mensageiro": [{"canal": "telegram", "user_id": "123456789", "telegram_username": "diretora_ana", "nome": "Diretora Ana", "role": "gestor", "ativo": true, "autorizado_em": "2026-07-13T00:00:00Z", "autorizado_por": "sistema"}]}',
                encoding="utf-8",
            )
            (root / "config/telas.map.json").write_text('{"tv_saguao": {"aliases": ["tv do saguao", "saguao"]}}', encoding="utf-8")
            (root / "config/dispositivos.json").write_text('{"tv_saguao": {"screen_id": "tv_saguao", "label": "TV do Saguão", "ip": "192.168.15.16", "ativo": true, "device_token": "token-1", "aliases": ["tv do saguao", "saguao"]}}', encoding="utf-8")
            (root / "state/telas.json").write_text('{"tv_saguao": {"tipo": "vazio", "src": "", "desde": ""}}', encoding="utf-8")
            (root / "state/mensagens.json").write_text('{"pendentes": []}', encoding="utf-8")
            (root / "state/dispositivos.json").write_text(_device_status_payload(), encoding="utf-8")

            service = SignalizacaoService(root=root)
            result = service.handle_text_command("gerar slide de aviso na tv do saguao: reuniao hoje as 18h", origin="painel_local", actor="diretor")

            self.assertEqual(result["status"], "ok")
            state = service.get_screen_state("tv_saguao")
            self.assertEqual(state["tipo"], "slide")
            self.assertTrue(str(state["src"]).startswith("gerado/"))

    def test_gestor_can_authorize_messenger_user(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for relative in ["config", "state", "content/biblioteca", "content/gerado", "logs"]:
                (root / relative).mkdir(parents=True, exist_ok=True)

            (root / "config/settings.yml").write_text(
                "porta: 8080\nmodo: local\npolling_segundos: 5\nflask_secret_key: teste\npicoclaw:\n  habilitado: true\n  bin: /home/admin/picoclaw_agent\n  modelo: antigravity\n  mensageiro: telegram\n",
                encoding="utf-8",
            )
            (root / "config/whitelist.json").write_text(
                '{"painel_local": [{"user": "diretor", "hash_senha": "plain:trocar123", "role": "gestor", "ativo": true}], "mensageiro": [{"canal": "telegram", "user_id": "123456789", "telegram_username": "diretora_ana", "nome": "Diretora Ana", "role": "gestor", "ativo": true, "autorizado_em": "2026-07-13T00:00:00Z", "autorizado_por": "sistema"}]}',
                encoding="utf-8",
            )
            (root / "config/telas.map.json").write_text('{"tv_saguao": {"aliases": ["tv do saguao", "saguao"]}}', encoding="utf-8")
            (root / "config/dispositivos.json").write_text('{"tv_saguao": {"screen_id": "tv_saguao", "label": "TV do Saguão", "ip": "192.168.15.16", "ativo": true, "device_token": "token-1", "aliases": ["tv do saguao", "saguao"]}}', encoding="utf-8")
            (root / "state/telas.json").write_text('{"tv_saguao": {"tipo": "vazio", "src": "", "desde": ""}}', encoding="utf-8")
            (root / "state/mensagens.json").write_text('{"pendentes": []}', encoding="utf-8")
            (root / "state/dispositivos.json").write_text(_device_status_payload(), encoding="utf-8")

            service = SignalizacaoService(root=root)
            result = service.handle_messenger_payload(
                {
                    "channel": "telegram",
                    "sender_id": "123456789",
                    "sender_username": "diretora_ana",
                    "sender_name": "Diretora Ana",
                    "text": "autorizar usuario @operador_tela no telegram",
                }
            )

            self.assertEqual(result["status"], "ok")
            autorizados = service.list_authorized_users()
            self.assertTrue(any(item.get("telegram_username") == "operador_tela" for item in autorizados))
            historico = service.list_authorization_history()
            self.assertTrue(any(entry.get("acao") == "autorizar_usuario" for entry in historico))

    def test_device_unavailable_blocks_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for relative in ["config", "state", "content/biblioteca", "content/gerado", "logs"]:
                (root / relative).mkdir(parents=True, exist_ok=True)

            (root / "config/settings.yml").write_text(
                "porta: 8080\nmodo: local\npolling_segundos: 5\nheartbeat_ttl_segundos: 1\nflask_secret_key: teste\npicoclaw:\n  habilitado: true\n  bin: /home/admin/picoclaw_agent\n  modelo: antigravity\n  mensageiro: telegram\n",
                encoding="utf-8",
            )
            (root / "config/whitelist.json").write_text(
                '{"painel_local": [{"user": "diretor", "hash_senha": "plain:trocar123", "role": "gestor", "ativo": true}], "mensageiro": []}',
                encoding="utf-8",
            )
            (root / "config/telas.map.json").write_text('{"tv_saguao": {"aliases": ["tv do saguao"]}}', encoding="utf-8")
            (root / "config/dispositivos.json").write_text('{"tv_saguao": {"screen_id": "tv_saguao", "label": "TV do Saguão", "ip": "192.168.15.16", "ativo": true, "device_token": "token-1", "aliases": ["tv do saguao"]}}', encoding="utf-8")
            (root / "state/telas.json").write_text('{"tv_saguao": {"tipo": "vazio", "src": "", "desde": ""}}', encoding="utf-8")
            (root / "state/mensagens.json").write_text('{"pendentes": []}', encoding="utf-8")
            (root / "state/dispositivos.json").write_text('{"items": {}}', encoding="utf-8")

            media_file = root / "content/biblioteca" / "avisos.png"
            media_file.write_bytes(b"fake-png")

            service = SignalizacaoService(root=root)
            result = service.apply_command(
                {"acao": "exibir", "midia": "biblioteca/avisos.png", "tela": "tv_saguao"},
                origin="painel_local",
                actor="diretor",
            )

            self.assertEqual(result["status"], "recusado")
            self.assertIn("TV nao encontrada/cadastrada", result["reason"])

    def test_hashed_password_login(self) -> None:
        from sinalizacao.server.auth import hash_password, verify_local_login
        hashed = hash_password("senha_segura_123")
        whitelist = {"painel_local": [{"user": "admin", "hash_senha": hashed, "ativo": True}]}
        
        self.assertTrue(verify_local_login(whitelist, "admin", "senha_segura_123"))
        self.assertFalse(verify_local_login(whitelist, "admin", "senha_errada"))

    def test_telegram_update_parsing(self) -> None:
        from sinalizacao.server.messenger_bridge import parse_telegram_update
        update = {
            "update_id": 99,
            "message": {
                "message_id": 101,
                "from": {"id": 123456789, "first_name": "Ana", "username": "diretora_ana"},
                "chat": {"id": 123456789},
                "text": "manda para a tv do saguao"
            }
        }
        event = parse_telegram_update(update)
        self.assertEqual(event.channel, "telegram")
        self.assertEqual(event.sender_id, "123456789")
        self.assertEqual(event.sender_username, "diretora_ana")
        self.assertEqual(event.text, "manda para a tv do saguao")


if __name__ == "__main__":
    unittest.main()

