from pathlib import Path

from dressing_assistant.config import AppConfig
from dressing_assistant.models import AssistantResult, OutfitProposal, ProposedOperation
from dressing_assistant.service import DressingService
from dressing_assistant.storage import save_wardrobe
from dressing_assistant.models import WardrobeItem


class FakeProvider:
    def __init__(self, result: AssistantResult) -> None:
        self.result = result

    def generate(self, prompt: str) -> AssistantResult:
        assert "当前用户消息" in prompt
        return self.result


def test_service_filters_invalid_outfit_ids(tmp_path: Path) -> None:
    config = AppConfig.from_data_dir(tmp_path)
    config.ensure_layout()
    save_wardrobe(config, [WardrobeItem(id="valid", name="白衬衫", category="top")])
    provider = FakeProvider(
        AssistantResult(
            reply="推荐完成",
            intent="recommend",
            outfits=[
                OutfitProposal(title="通勤", item_ids=["valid", "invented"], reason="干净")
            ],
        )
    )

    result = DressingService(config, provider=provider).handle_turn(
        message="通勤穿什么",
        recent_messages=[],
        session_summary="",
        temporary_exclusions=[],
        last_outfit_item_ids=[],
    )

    assert result.outfits[0].item_ids == ["valid"]


def test_service_applies_pending_operation(tmp_path: Path) -> None:
    config = AppConfig.from_data_dir(tmp_path)
    config.ensure_layout()
    save_wardrobe(config, [])
    operation = ProposedOperation(
        target="wardrobe",
        op="add",
        item={"id": "new", "name": "新衬衫", "category": "top"},
    )

    results = DressingService(config).apply_operations([operation])

    assert results[0].ok
    assert config.wardrobe_path.read_text(encoding="utf-8").find("新衬衫") >= 0
