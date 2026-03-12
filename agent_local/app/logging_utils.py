from __future__ import annotations

from datetime import datetime
from pathlib import Path


def utc_now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def append_log(log_path: Path, msg: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    line = f"[{utc_now_iso()}] {msg}\n"
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(line)
