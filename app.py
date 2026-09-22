from __future__ import annotations

import streamlit as st

from dressing_assistant.config import AppConfig
from dressing_assistant.presentation import format_assistant_message
from dressing_assistant.service import DressingService
from dressing_assistant.storage import (
    atomic_write_text,
    ensure_layout,
    load_profile_document,
    load_wardrobe,
    render_profile_document,
)


st.set_page_config(
    page_title="Dressing",
    page_icon="👗",
    layout="wide",
    initial_sidebar_state="expanded",
)


def get_config() -> AppConfig:
    config = AppConfig.from_data_dir()
    ensure_layout(config)
    return config


def init_state() -> None:
    defaults = {
        "messages": [],
        "session_summary": "",
        "temporary_exclusions": [],
        "last_outfit_item_ids": [],
        "pending_operations": [],
        "reload_nonce": 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def submit_turn(config: AppConfig, message: str) -> None:
    service = DressingService(config)
    recent = st.session_state.messages[-config.max_recent_messages:]
    with st.spinner("正在读取 Profile 与衣柜..."):
        result = service.handle_turn(
            message=message,
            recent_messages=recent,
            session_summary=st.session_state.session_summary,
            temporary_exclusions=st.session_state.temporary_exclusions,
            last_outfit_item_ids=st.session_state.last_outfit_item_ids,
        )

    st.session_state.messages.append({"role": "user", "content": message})
    _, _, wardrobe = service.load_state()
    rendered = format_assistant_message(result, wardrobe)
    st.session_state.messages.append({"role": "assistant", "content": rendered})
    st.session_state.session_summary = result.session_summary or st.session_state.session_summary
    st.session_state.temporary_exclusions = list(
        dict.fromkeys([*st.session_state.temporary_exclusions, *result.temporary_exclusions])
    )
    st.session_state.last_outfit_item_ids = [
        item_id
        for outfit in result.outfits
        for item_id in outfit.item_ids
    ]
    st.session_state.pending_operations = [
        operation.model_dump(mode="python")
        for operation in result.proposed_operations
    ]


def confirm_pending(config: AppConfig) -> None:
    from dressing_assistant.models import ProposedOperation

    operations = [
        ProposedOperation.model_validate(raw)
        for raw in st.session_state.pending_operations
    ]
    service = DressingService(config)
    results = service.apply_operations(operations)
    text_lines = ["写入结果："]
    for result in results:
        text_lines.append(f"- {'成功' if result.ok else '失败'}：{result.message}")
    st.session_state.messages.append(
        {"role": "assistant", "content": "\n".join(text_lines)}
    )
    st.session_state.pending_operations = []
    st.session_state.last_outfit_item_ids = []


config = get_config()
init_state()

st.title("Dressing")
st.caption("本地文件驱动的私人穿搭助手")

with st.sidebar:
    st.subheader("运行状态")
    st.code(str(config.data_dir), language=None)
    st.caption(f"Profile: {config.profile_path.name}")
    st.caption(f"Wardrobe: {config.wardrobe_path.name}")
    if st.button("重新读取文件", use_container_width=True):
        st.session_state.reload_nonce += 1
        st.rerun()
    st.divider()
    if st.button("清空当前对话", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_summary = ""
        st.session_state.temporary_exclusions = []
        st.session_state.last_outfit_item_ids = []
        st.session_state.pending_operations = []
        st.rerun()

chat_tab, profile_tab, wardrobe_tab, settings_tab = st.tabs(
    ["穿搭助手", "个人资料", "衣柜管理", "设置"]
)

with chat_tab:
    for entry in st.session_state.messages:
        with st.chat_message(entry["role"]):
            st.markdown(entry["content"])

    if st.session_state.pending_operations:
        st.warning("有尚未写入的衣柜修改。完成后会先备份原文件。")
        col_confirm, col_cancel = st.columns([1, 1])
        if col_confirm.button("确认写入", type="primary", use_container_width=True):
            confirm_pending(config)
            st.rerun()
        if col_cancel.button("取消修改", use_container_width=True):
            st.session_state.pending_operations = []
            st.session_state.messages.append(
                {"role": "assistant", "content": "已取消本次修改。"}
            )
            st.rerun()

    prompt = st.chat_input("例如：今天 18 度，有点风，通勤穿什么？")
    if prompt:
        submit_turn(config, prompt)
        st.rerun()

with profile_tab:
    st.subheader("Profile")
    st.caption("直接编辑文档；保存前自动备份。推荐时只自动发送穿搭影响摘要。")
    meta, body = load_profile_document(config)
    rendered_profile = render_profile_document(meta, body) if meta or body else ""
    edited_profile = st.text_area(
        "profile.md",
        value=rendered_profile,
        height=560,
        key=f"profile_editor_{st.session_state.reload_nonce}",
    )
    if st.button("保存 Profile", type="primary"):
        atomic_write_text(
            config.profile_path,
            edited_profile.rstrip() + "\n",
            backups_dir=config.backups_dir,
        )
        st.session_state.reload_nonce += 1
        st.success("Profile 已保存。")
        st.rerun()

with wardrobe_tab:
    st.subheader("衣柜")
    items = load_wardrobe(config)
    if items:
        st.dataframe(
            [
                {
                    "ID": item.id,
                    "名称": item.name,
                    "品类": item.category,
                    "颜色": "、".join(item.colors),
                    "材质": "、".join(item.materials),
                    "厚薄": item.thickness,
                    "季节": "、".join(item.seasons),
                    "场景": "、".join(item.scenes),
                    "状态": item.inference_status,
                }
                for item in items
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("衣柜为空。")

    raw = config.wardrobe_path.read_text(encoding="utf-8") if config.wardrobe_path.exists() else ""
    edited = st.text_area("wardrobe.yaml（高级编辑）", value=raw, height=500)
    if st.button("保存 wardrobe.yaml", type="primary"):
        try:
            import yaml

            parsed = yaml.safe_load(edited) or {}
            if not isinstance(parsed, dict) or not isinstance(parsed.get("items"), list):
                raise ValueError("顶层必须包含 items 列表")
            atomic_write_text(
                config.wardrobe_path,
                edited.rstrip() + "\n",
                backups_dir=config.backups_dir,
            )
            st.session_state.reload_nonce += 1
            st.success("衣柜文件已保存。")
            st.rerun()
        except Exception as exc:  # noqa: BLE001
            st.error(f"YAML 校验失败：{exc}")

with settings_tab:
    st.subheader("设置")
    st.write("配置文件：")
    st.code(str(config.config_path), language=None)
    st.write("Codex 可执行文件：")
    st.code(config.codex_binary, language=None)
    st.write("专用 CODEX_HOME：")
    st.code(str(config.codex_home or "当前 Codex 默认配置"), language=None)
    st.write("Codex Profile：")
    st.code(config.codex_profile or "未指定", language=None)
    st.write("模型：")
    st.code(config.codex_model or "使用该 CODEX_HOME 的默认模型", language=None)
    st.info("第一版不保存聊天历史；关闭或清空会话后只保留 Profile 和衣柜文件。")
