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
                print(f"[*] Enviando Heartbeat para o Gestor (ID: {self.config.exibidor_id})...")
                heartbeat = send_heartbeat(
                    self.config.gestor_base_url,
                    {
                        "screen_id": self.config.exibidor_id,
                        "device_ip": self.config.device_ip,
                        "device_token": self.config.device_token,
                    },
                )
                if heartbeat.status != "ok":
                    print(f"[!] Heartbeat recusado pelo Gestor: {heartbeat.reason}")
                    self.state.mark_error(heartbeat.reason or "heartbeat recusado")
                    save_state(self.state_file, self.state)
                    return {"status": "erro", "reason": heartbeat.reason or "heartbeat recusado"}
                print("[+] Heartbeat aceito com sucesso!")
            
            print("[*] Buscando estado atual da tela no Gestor...")
            screen_state = fetch_screen_state(self.config.gestor_base_url, self.config.exibidor_id)
        except Exception as exc:  # noqa: BLE001 - player precisa continuar mesmo sem Gestor
            print(f"[!] Erro ao conectar com o Gestor: {exc}")
            self.state.mark_error(f"gestor indisponivel: {exc}")
            save_state(self.state_file, self.state)
            return {"status": "erro", "reason": "gestor indisponivel"}

        if screen_state.src == self.state.last_seen_src and screen_state.tipo == self.state.last_seen_tipo:
            print("[~] Sem alteracao no conteudo da tela.")
            return {"status": "ok", "reason": "sem alteracao"}

        if screen_state.tipo == "vazio" or not screen_state.src:
            print("[-] Comando recebido: Limpar tela.")
            placeholder = show_placeholder(f"{self.config.exibidor_id}: tela limpa", self.config.cache_dir / f"{self.config.exibidor_id}_vazio.txt")
            self.state.last_seen_src = ""
            self.state.last_seen_tipo = "vazio"
            self.state.last_downloaded_file = str(placeholder)
            self.state.last_updated_at = self.state.last_updated_at or ""
            self.state.last_error = ""
            save_state(self.state_file, self.state)
            return {"status": "ok", "reason": "tela limpa"}

        if screen_state.tipo in {"imagem", "slide", "playlist"} and screen_state.src:
            print(f"[+] Nova midia encontrada: {screen_state.src} ({screen_state.tipo})")
            destination = self.config.cache_dir / Path(screen_state.src).name
            try:
                print(f"[*] Baixando midia: {screen_state.src}...")
                downloaded = download_media(self.config.gestor_base_url, screen_state.src, destination)
                print(f"[+] Download concluido! Exibindo imagem via fbi...")
                displayed = display_image(downloaded, command=self.config.display_command)
                self.state.mark_download(screen_state.src, screen_state.tipo, str(downloaded))
                if not displayed:
                    print("[!] Alerta: O comando de exibicao local (fbi) nao foi encontrado no sistema ou falhou.")
                    self.state.mark_error("comando de exibicao nao encontrado")
                save_state(self.state_file, self.state)
                return {"status": "ok", "reason": "conteudo atualizado"}
            except Exception as exc:  # noqa: BLE001 - o player precisa degradar
                print(f"[!] Falha ao baixar ou exibir: {exc}")
                self.state.mark_error(f"falha ao baixar/exibir: {exc}")
                save_state(self.state_file, self.state)
                return {"status": "erro", "reason": "falha ao baixar/exibir"}

        print(f"[!] Tipo de tela nao suportado: {screen_state.tipo}")
        self.state.mark_error(f"tipo nao suportado: {screen_state.tipo}")
        save_state(self.state_file, self.state)
        return {"status": "erro", "reason": "tipo nao suportado"}

    def run_forever(self) -> None:
        while True:
            self.step()
            time.sleep(self.config.polling_segundos)

if __name__ == "__main__":
    import sys
    from .config import load_exibidor_config
    
    env_file = Path("exibidor.env")
    print(f"[*] Iniciando Player Exibidor. Lendo {env_file}...")
    
    if not env_file.exists():
        print(f"[!] Erro: Arquivo {env_file} nao encontrado. O player precisa deste arquivo para iniciar.")
        sys.exit(1)
        
    config = load_exibidor_config(env_file)
    player = ExibidorPlayer(config)
    player.run_forever()
