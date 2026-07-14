from __future__ import annotations

from pathlib import Path
import shutil
import subprocess


def display_image(image_path: Path, command: str = "fbi") -> bool:
    executable = shutil.which(command)
    if not executable:
        return False

    try:
        subprocess.run(
            [executable, "-T", "1", "-noverbose", "-a", str(image_path)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def show_placeholder(message: str, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(message, encoding="utf-8")
    return output_path
