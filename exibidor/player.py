from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import time

from .client import fetch_screen_state, is_reachable, download_media, send_heartbeat
from .config import ExibidorConfig
from .display import display_image, show_placeholder
from .state import ExibidorState, load_state, save_state


@dataclass
class ExibidorPlayer:
    config: ExibidorConfig

    def __post_init__(self) -> None:
        self.config.cache_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.config.cache_dir / f"{self.config.exibidor_id}.json"
        self.state = load_state(self.state_file, self.config.exibidor_id)

    def step(self) -> dict[str, str]:
        try:
            if self.config.device_token:
                heartbeat = send_heartbeat(
                    self.config.gestor_base_url,
                    {
                        "screen_id": self.config.exibidor_id,
                        "device_ip": self.config.device_ip,
                        "device_token": self.config.device_token,
                    },
                )
                if heartbeat.status != "ok":
                    self.state.mark_error(heartbeat.reason or "heartbeat recusado")
                    save_state(self.state_file, self.state)
                    return {"status": "erro", "reason": heartbeat.reason or "heartbeat recusado"}
            screen_state = fetch_screen_state(self.config.gestor_base_url, self.config.exibidor_id)
        except Exception as exc:  # noqa: BLE001 - player precisa continuar mesmo sem Gestor
            self.state.mark_error(f"gestor indisponivel: {exc}")
            save_state(self.state_file, self.state)
            return {"status": "erro", "reason": "gestor indisponivel"}

        if screen_state.src == self.state.last_seen_src and screen_state.tipo == self.state.last_seen_tipo:
            return {"status": "ok", "reason": "sem alteracao"}

        if screen_state.tipo == "vazio" or not screen_state.src:
            placeholder = show_placeholder(f"{self.config.exibidor_id}: tela limpa", self.config.cache_dir / f"{self.config.exibidor_id}_vazio.txt")
            self.state.last_seen_src = ""
            self.state.last_seen_tipo = "vazio"
            self.state.last_downloaded_file = str(placeholder)
            self.state.last_updated_at = self.state.last_updated_at or ""
            self.state.last_error = ""
            save_state(self.state_file, self.state)
            return {"status": "ok", "reason": "tela limpa"}

        if screen_state.tipo in {"imagem", "slide"} and screen_state.src:
            destination = self.config.cache_dir / Path(screen_state.src).name
            try:
                downloaded = download_media(self.config.gestor_base_url, screen_state.src, destination)
                displayed = display_image(downloaded, command=self.config.display_command)
                self.state.mark_download(screen_state.src, str(downloaded))
                if not displayed:
                    self.state.mark_error("comando de exibicao nao encontrado")
                save_state(self.state_file, self.state)
                return {"status": "ok", "reason": "conteudo atualizado"}
            except Exception as exc:  # noqa: BLE001 - o player precisa degradar
                self.state.mark_error(f"falha ao baixar/exibir: {exc}")
                save_state(self.state_file, self.state)
                return {"status": "erro", "reason": "falha ao baixar/exibir"}

        self.state.mark_error(f"tipo nao suportado: {screen_state.tipo}")
        save_state(self.state_file, self.state)
        return {"status": "erro", "reason": "tipo nao suportado"}

    def run_forever(self) -> None:
        while True:
            self.step()
            time.sleep(self.config.polling_segundos)
