#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dressing_assistant.config import AppConfig  # noqa: E402
from dressing_assistant.llm import resolve_codex_binary  # noqa: E402


def main() -> int:
    config = AppConfig.from_data_dir()
    binary = resolve_codex_binary(config.codex_binary)
    if not binary:
        print("FAIL: codex executable not found")
        return 1

    env = None
    if config.codex_home is not None:
        import os

        env = os.environ.copy()
        env["CODEX_HOME"] = str(config.codex_home)

    login = subprocess.run(
        [binary, "login", "status"],
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    login_text = (login.stdout + login.stderr).strip()
    print(f"LOGIN: {login_text or 'unknown'}")

    with tempfile.TemporaryDirectory(prefix="dressing-model-check-") as tmp:
        command = [
            binary,
            "exec",
            "--ephemeral",
            "--sandbox",
            "read-only",
            "--skip-git-repo-check",
            "--color",
            "never",
            "-C",
            tmp,
        ]
        if config.codex_profile:
            command.extend(["-p", config.codex_profile])
        if config.codex_model:
            command.extend(["-m", config.codex_model])
        command.append("-")
        result = subprocess.run(
            command,
            input="只回复 Dressing model check OK",
            text=True,
            capture_output=True,
            env=env,
            timeout=config.codex_timeout_seconds,
            check=False,
        )

    combined = "\n".join(part for part in (result.stdout, result.stderr) if part)
    model_match = re.search(r"^model:\s*(.+)$", combined, re.MULTILINE)
    provider_match = re.search(r"^provider:\s*(.+)$", combined, re.MULTILINE)
    model = model_match.group(1).strip() if model_match else "unknown"
    provider = provider_match.group(1).strip() if provider_match else "unknown"

    print(f"MODEL: {model}")
    print(f"PROVIDER: {provider}")
    if result.returncode != 0:
        print("FAIL: model probe request failed")
        return 1
    if provider != "openai" or not model.lower().startswith("gpt"):
        print("FAIL: Dressing is not using an OpenAI GPT model")
        return 1

    print("PASS: Dressing is using an OpenAI GPT model")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
