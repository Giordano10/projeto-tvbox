from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess

_current_viewer_proc: subprocess.Popen | None = None

def _kill_previous() -> None:
    global _current_viewer_proc
    if _current_viewer_proc is not None:
        try:
            _current_viewer_proc.terminate()
            _current_viewer_proc.wait(timeout=2)
        except Exception:
            try:
                _current_viewer_proc.kill()
            except Exception:
                pass
        _current_viewer_proc = None

def display_image(image_path: Path, command: str = "fbi") -> bool:
    global _current_viewer_proc
    _kill_previous()

    executable = shutil.which(command)
    if executable:
        try:
            _current_viewer_proc = subprocess.Popen(
                [executable, "-T", "1", "-noverbose", "-a", str(image_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            pass

    # Alternative Linux viewers
    for alt in ["feh", "mpv", "eog"]:
        alt_exec = shutil.which(alt)
        if alt_exec:
            try:
                if alt == "feh":
                    args = [alt_exec, "-F", "-Z", str(image_path)]
                else:
                    args = [alt_exec, str(image_path)]
                _current_viewer_proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
            except Exception:
                continue

    # Fallback para ambiente Windows / Desktop local de desenvolvimento
    if hasattr(os, "startfile"):
        try:
            subprocess.run(["taskkill", "/F", "/IM", "Microsoft.Photos.exe"], capture_output=True)
            subprocess.run(["taskkill", "/F", "/IM", "PhotosApp.exe"], capture_output=True)
            os.startfile(image_path)
            return True
        except Exception:
            pass

    return False


def show_placeholder(message: str, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(message, encoding="utf-8")
    return output_path
