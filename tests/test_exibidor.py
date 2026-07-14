from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from exibidor.config import load_exibidor_config
from exibidor.player import ExibidorPlayer


class ExibidorTests(unittest.TestCase):
    def test_load_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config_file = root / "exibidor.conf"
            config_file.write_text(
                "exibidor_id=tv_saguao\ngestor_base_url=http://gestor.local:8080\ndevice_ip=192.168.15.16\ndevice_token=token-1\ncache_dir=cache\npolling_segundos=2\nheartbeat_segundos=1\ndisplay_command=fbi\n",
                encoding="utf-8",
            )

            config = load_exibidor_config(config_file)

            self.assertEqual(config.exibidor_id, "tv_saguao")
            self.assertEqual(config.device_ip, "192.168.15.16")
            self.assertEqual(config.polling_segundos, 2)

    def test_step_without_gestor_does_not_crash(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cache_dir = root / "cache"
            cache_dir.mkdir(parents=True, exist_ok=True)
            config_file = root / "exibidor.conf"
            config_file.write_text(
                f"exibidor_id=tv_saguao\ngestor_base_url=http://127.0.0.1:9\ndevice_ip=192.168.15.16\ndevice_token=token-1\ncache_dir={cache_dir.as_posix()}\npolling_segundos=1\nheartbeat_segundos=1\ndisplay_command=fbi\n",
                encoding="utf-8",
            )
            config = load_exibidor_config(config_file)
            player = ExibidorPlayer(config)

            result = player.step()

            self.assertEqual(result["status"], "erro")


if __name__ == "__main__":
    unittest.main()
