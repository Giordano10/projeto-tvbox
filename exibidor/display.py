from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess


def display_image(image_path: Path, command: str = "fbi") -> bool:
    executable = shutil.which(command)
    if executable:
        try:
            subprocess.run(
                [executable, "-T", "1", "-noverbose", "-a", str(image_path)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

    # Alternative Linux viewers
    for alt in ["feh", "mpv", "eog"]:
        alt_exec = shutil.which(alt)
        if alt_exec:
            try:
                subprocess.run([alt_exec, str(image_path)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
            except Exception:
                continue

    # Fallback para ambiente Windows / Desktop local de desenvolvimento
    if hasattr(os, "startfile"):
        try:
            os.startfile(image_path)
            return True
        except Exception:
            pass

    return False


def show_placeholder(message: str, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(message, encoding="utf-8")
    return output_path
