from __future__ import annotations

from typing import Any

from .config import AppConfig
from .llm import CodexCLIProvider, LLMError
from .models import AppliedOperation, AssistantResult, ProposedOperation, WardrobeItem
from .prompting import build_prompt
from .storage import (
    load_profile_document,
    load_wardrobe,
    save_wardrobe,
)
from .wardrobe import apply_operation, normalize_operation


class DressingService:
    def __init__(self, config: AppConfig, provider: CodexCLIProvider | None = None) -> None:
        self.config = config
        self.provider = provider or CodexCLIProvider(config)

    def load_state(self) -> tuple[dict[str, Any], str, list[WardrobeItem]]:
        profile_meta, profile_body = load_profile_document(self.config)
        wardrobe = load_wardrobe(self.config)
        return profile_meta, profile_body, wardrobe

    def handle_turn(
        self,
        *,
        message: str,
        recent_messages: list[dict[str, str]],
        session_summary: str,
        temporary_exclusions: list[str],
        last_outfit_item_ids: list[str],
    ) -> AssistantResult:
        profile_meta, profile_body, items = self.load_state()
        prompt = build_prompt(
            message=message,
            recent_messages=recent_messages,
            session_summary=session_summary,
            profile_meta=profile_meta,
            profile_body=profile_body,
            items=items,
            temporary_exclusions=temporary_exclusions,
            last_outfit_item_ids=last_outfit_item_ids,
        )
        try:
            result = self.provider.generate(prompt)
        except LLMError as exc:
            return AssistantResult(
                reply=f"暂时无法调用模型：{exc}",
                intent="chat",
                session_summary=session_summary,
            )

        valid_ids = {item.id for item in items}
        clean_outfits = []
        for outfit in result.outfits:
            ids = [item_id for item_id in outfit.item_ids if item_id in valid_ids]
            if ids:
                clean_outfits.append(outfit.model_copy(update={"item_ids": ids}))

        clean_ops = [
            normalize_operation(op)
            for op in result.proposed_operations
            if op.target == "wardrobe"
        ]
        clean_exclusions = [
            item_id for item_id in result.temporary_exclusions if item_id in valid_ids
        ]

        return result.model_copy(
            update={
                "outfits": clean_outfits,
                "proposed_operations": clean_ops,
                "temporary_exclusions": clean_exclusions,
            }
        )

    def apply_operations(self, operations: list[ProposedOperation]) -> list[AppliedOperation]:
        items = load_wardrobe(self.config)
        results: list[AppliedOperation] = []
        for operation in operations:
            try:
                items, message = apply_operation(items, normalize_operation(operation))
                results.append(AppliedOperation(ok=True, message=message))
            except Exception as exc:  # noqa: BLE001
                results.append(AppliedOperation(ok=False, message=str(exc)))
        if any(result.ok for result in results):
            save_wardrobe(self.config, items)
        return results
