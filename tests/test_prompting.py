from dressing_assistant.models import WardrobeItem
from dressing_assistant.prompting import build_prompt

PROFILE = {
    "basic": {"height_cm": 170, "weight_kg": 60},
    "style": {"avoid": ["荧光色"]},
    "appearance": {"skin_tone": "中性肤色", "face_summary": "椭圆脸"},
    "facial": {"structure": "中庭偏长"},
}


def test_prompt_contains_core_but_not_facial_detail_for_regular_request() -> None:
    prompt = build_prompt(
        message="今天18度，通勤穿什么",
        recent_messages=[],
        session_summary="",
        profile_meta=PROFILE,
        profile_body="私人备注",
        items=[WardrobeItem(id="top1", name="白色衬衫", category="top")],
        temporary_exclusions=[],
        last_outfit_item_ids=[],
    )
    assert "中性肤色" in prompt
    assert "中庭偏长" not in prompt


def test_prompt_includes_detail_when_appearance_is_relevant() -> None:
    prompt = build_prompt(
        message="我的脸型适合什么领口和配色",
        recent_messages=[],
        session_summary="",
        profile_meta=PROFILE,
        profile_body="私人备注",
        items=[WardrobeItem(id="top1", name="白色衬衫", category="top")],
        temporary_exclusions=[],
        last_outfit_item_ids=[],
    )
    assert "中庭偏长" in prompt
