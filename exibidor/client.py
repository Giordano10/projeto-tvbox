from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
import json
import shutil


@dataclass(frozen=True)
class ScreenState:
    tela: str
    tipo: str
    src: str
    desde: str


@dataclass(frozen=True)
class HeartbeatResult:
    status: str
    reason: str = ""


def build_screen_state_url(base_url: str, screen_id: str) -> str:
    return f"{base_url.rstrip('/')}/api/tela/{quote(screen_id)}/"


def build_content_url(base_url: str, relative_src: str) -> str:
    normalized = relative_src.lstrip("/")
    return f"{base_url.rstrip('/')}/conteudo/{quote(normalized)}"


def build_heartbeat_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}/api/dispositivos/heartbeat"


def fetch_screen_state(base_url: str, screen_id: str, timeout_seconds: int = 5) -> ScreenState:
    request = Request(build_screen_state_url(base_url, screen_id), headers={"Accept": "application/json"})
    with urlopen(request, timeout=timeout_seconds) as response:
        payload = json.loads(response.read().decode("utf-8"))
    estado = payload.get("estado") or {}
    return ScreenState(
        tela=str(payload.get("tela", screen_id)),
        tipo=str(estado.get("tipo", "vazio")),
        src=str(estado.get("src", "")),
        desde=str(estado.get("desde", "")),
    )


def download_media(base_url: str, relative_src: str, destination: Path, timeout_seconds: int = 10) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = Request(build_content_url(base_url, relative_src), headers={"Accept": "*/*"})
    with urlopen(request, timeout=timeout_seconds) as response, destination.open("wb") as handle:
        shutil.copyfileobj(response, handle)
    return destination


def send_heartbeat(base_url: str, payload: dict[str, str], timeout_seconds: int = 5) -> HeartbeatResult:
    request = Request(
        build_heartbeat_url(base_url),
        data=json.dumps(payload).encode("utf-8"),
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        method="POST",
    )
    
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            body = json.loads(response.read().decode("utf-8"))
            return HeartbeatResult(
                status=str(body.get("status", "erro")), 
                reason=str(body.get("reason", ""))
            )
    except HTTPError as e:
        return HeartbeatResult(status="erro", reason=f"Erro HTTP {e.code}")
    except URLError as e:
        return HeartbeatResult(status="erro", reason=f"Falha de rede: {e.reason}")
    except Exception as e:
        return HeartbeatResult(status="erro", reason=f"Erro interno: {e}")


def is_reachable(base_url: str, timeout_seconds: int = 3) -> bool:
    request = Request(base_url.rstrip("/") + "/", headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=timeout_seconds):
            return True
    except (HTTPError, URLError, TimeoutError):
        return False
