from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class JsonStore:
    path: Path

    def read(self, default: Any | None = None) -> Any:
        if not self.path.exists():
            return default
        with self.path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def write(self, data: Any) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.path.with_suffix(self.path.suffix + ".tmp")
        with temporary_path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, self.path)


def load_json(path: Path, default: Any) -> Any:
    return JsonStore(path).read(default)


def save_json(path: Path, data: Any) -> None:
    JsonStore(path).write(data)
