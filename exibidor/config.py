from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExibidorConfig:
    exibidor_id: str
    gestor_base_url: str
    device_ip: str
    device_token: str
    cache_dir: Path
    polling_segundos: int = 5
    heartbeat_segundos: int = 10
    display_command: str = "fbi"


def load_exibidor_config(path: Path) -> ExibidorConfig:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()

    cache_dir = Path(values.get("cache_dir", "cache"))
    return ExibidorConfig(
        exibidor_id=values.get("exibidor_id", "tv_saguao"),
        gestor_base_url=values.get("gestor_base_url", "http://gestor.local:8080").rstrip("/"),
        device_ip=values.get("device_ip", ""),
        device_token=values.get("device_token", ""),
        cache_dir=cache_dir,
        polling_segundos=int(values.get("polling_segundos", "5")),
        heartbeat_segundos=int(values.get("heartbeat_segundos", "10")),
        display_command=values.get("display_command", "fbi"),
    )
