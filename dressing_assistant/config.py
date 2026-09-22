from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

DEFAULT_DATA_DIR = Path.home() / "Documents" / "WardrobeAssistantData"


@dataclass(frozen=True)
class AppConfig:
    data_dir: Path
    profile_path: Path
    wardrobe_path: Path
    config_path: Path
    backups_dir: Path
    codex_binary: str
    codex_home: Path | None = None
    codex_profile: str | None = None
    codex_model: str | None = None
    codex_timeout_seconds: int = 180
    max_recent_messages: int = 6

    @classmethod
    def from_data_dir(cls, data_dir: str | Path | None = None) -> "AppConfig":
        chosen = Path(
            data_dir
            or os.environ.get("DRESSING_DATA_DIR")
            or DEFAULT_DATA_DIR
        ).expanduser().resolve()

        raw: dict[str, Any] = {}
        config_path = chosen / "config.yaml"
        if config_path.exists():
            loaded = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
            if not isinstance(loaded, dict):
                raise ValueError("config.yaml 顶层必须是映射结构")
            raw = loaded

        llm = raw.get("llm") or {}
        context = raw.get("context") or {}
        default_binary = str(
            Path("/Applications/ChatGPT.app/Contents/Resources/codex")
        )

        return cls(
            data_dir=chosen,
            profile_path=chosen / "profile.md",
            wardrobe_path=chosen / "wardrobe.yaml",
            config_path=config_path,
            backups_dir=chosen / "backups",
            codex_binary=str(llm.get("codex_binary") or default_binary),
            codex_home=(Path(llm["codex_home"]).expanduser().resolve() if llm.get("codex_home") else None),
            codex_profile=llm.get("profile") or None,
            codex_model=llm.get("model") or None,
            codex_timeout_seconds=int(llm.get("timeout_seconds") or 180),
            max_recent_messages=int(context.get("max_recent_messages") or 6),
        )

    def ensure_layout(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.backups_dir.mkdir(parents=True, exist_ok=True)
        if self.codex_home is not None:
            self.codex_home.mkdir(parents=True, exist_ok=True)
        if not self.config_path.exists():
            write_default_config(self.config_path)


def write_default_config(path: "Path | str") -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    content = """version: 1
llm:
  provider: codex_cli
  codex_binary: /Applications/ChatGPT.app/Contents/Resources/codex
  codex_home: null
  profile: null
  model: null
  timeout_seconds: 180
context:
  max_recent_messages: 6
"""
    target.write_text(content, encoding="utf-8")
