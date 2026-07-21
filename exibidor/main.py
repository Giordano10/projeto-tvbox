from __future__ import annotations

from pathlib import Path
import sys

from .config import load_exibidor_config
from .player import ExibidorPlayer


def main() -> int:
    base_dir = Path(__file__).resolve().parents[0]
    config_file = base_dir / "config" / "exibidor.conf"
    if not config_file.exists():
        print(f"configuracao nao encontrada: {config_file}")
        return 1

    config = load_exibidor_config(config_file)
    player = ExibidorPlayer(config)
    player.run_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
