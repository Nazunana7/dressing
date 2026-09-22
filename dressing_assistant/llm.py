from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from .config import AppConfig
from .models import AssistantResult


class LLMError(RuntimeError):
    pass


def resolve_codex_binary(configured: str) -> str | None:
    candidates = [
        os.environ.get("DRESSING_CODEX_BIN"),
        configured,
        shutil.which("codex"),
        "/Applications/ChatGPT.app/Contents/Resources/codex",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(Path(candidate))
    return None


class CodexCLIProvider:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def generate(self, prompt: str) -> AssistantResult:
        binary = resolve_codex_binary(self.config.codex_binary)
        if not binary:
            raise LLMError(
                "找不到 codex 可执行文件。请在 data/config.yaml 中设置 llm.codex_binary。"
            )

        with tempfile.TemporaryDirectory(prefix="dressing-codex-") as tmp:
            tmp_path = Path(tmp)
            output_path = tmp_path / "response.json"

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
                str(tmp_path),
                "--output-last-message",
                str(output_path),
            ]
            if self.config.codex_model:
                command.extend(["-m", self.config.codex_model])
            command.append("-")

            try:
                completed = subprocess.run(
                    command,
                    input=prompt,
                    text=True,
                    capture_output=True,
                    timeout=self.config.codex_timeout_seconds,
                    cwd=tmp_path,
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                raise LLMError("模型请求超时，请稍后重试或缩小请求范围。") from exc

            if completed.returncode != 0:
                detail = (completed.stderr or completed.stdout or "").strip()
                detail = detail.splitlines()[-1] if detail else "未知错误"
                raise LLMError(f"Codex 调用失败: {detail}")

            if not output_path.exists():
                raw_stdout = (completed.stdout or "").strip()
                if not raw_stdout:
                    raise LLMError("Codex 没有返回结构化结果。")
                return AssistantResult.model_validate_json(raw_stdout)

            raw = output_path.read_text(encoding="utf-8").strip()
            if not raw:
                raise LLMError("Codex 返回了空结果。")
            try:
                return AssistantResult.model_validate_json(raw)
            except Exception as exc:  # noqa: BLE001
                candidate = raw[raw.find("{") : raw.rfind("}") + 1]
                try:
                    return AssistantResult.model_validate_json(candidate)
                except Exception:
                    return AssistantResult(
                        reply=raw,
                        intent="chat",
                    )
