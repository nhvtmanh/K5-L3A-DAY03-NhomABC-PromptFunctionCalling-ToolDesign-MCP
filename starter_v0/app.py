from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import streamlit as st

from chat import (
    execute_tool_call,
    json_text,
    now_iso,
    run_model_tool_loop,
    trim_history,
    write_transcript,
)
from env_loader import load_lab_env
from providers import make_provider
from providers.base import ToolCall
from tools import TOOL_FUNCTIONS, load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version


ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"
PROVIDER_OPTIONS = ["openrouter", "openai", "deepseek", "anthropic", "gemini", "ollama"]

load_lab_env(ROOT)
st.set_page_config(page_title="Research Agent", page_icon="🔎", layout="centered")


def new_transcript(provider_name: str, model_name: str, version: str) -> dict[str, Any]:
    artifact_version = build_artifact_version(
        version,
        ARTIFACTS_DIR / "system_prompt.md",
        ARTIFACTS_DIR / "tools.yaml",
    )
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = f"{version}_{provider_name}_{timestamp}_{uuid4().hex[:8]}"
    return {
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact_version),
        "provider": provider_name,
        "model": model_name,
        "system_prompt": str(ARTIFACTS_DIR / "system_prompt.md"),
        "tools": str(ARTIFACTS_DIR / "tools.yaml"),
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }


def ui_tool_executor(call: ToolCall) -> dict[str, Any]:
    if call.name == "send" and call.args.get("confirmed") is True:
        return {
            "tool": call.name,
            "args": call.args,
            "result": {
                "status": "needs_ui_confirmation",
                "message": "Sending requires an explicit confirmation in the interface.",
            },
        }
    return execute_tool_call(call)


def get_pending_send(tool_events: list[dict[str, Any]]) -> dict[str, Any] | None:
    for event in tool_events:
        result = event.get("result")
        if event.get("tool") == "send" and isinstance(result, dict):
            if result.get("status") == "needs_ui_confirmation":
                return event
    return None


def save_current_transcript() -> Path:
    transcript = st.session_state.transcript
    path = TRANSCRIPTS_DIR / f"{transcript['transcript_id']}.transcript.json"
    write_transcript(path, transcript)
    return path


if "conversation" not in st.session_state:
    st.session_state.conversation = []
if "transcript" not in st.session_state:
    default_provider = make_provider("openrouter")
    st.session_state.transcript = new_transcript(
        "openrouter",
        default_provider.default_model,
        "ui-demo",
    )
if "pending_send" not in st.session_state:
    st.session_state.pending_send = None

st.title("🔎 Research Agent")
st.caption("Tìm kiếm web, bài đăng, paper và chính sách nội bộ — có trích nguồn.")

with st.sidebar:
    st.header("Cấu hình")
    config_disabled = bool(st.session_state.conversation)
    provider_name = st.selectbox(
        "Model provider",
        PROVIDER_OPTIONS,
        index=PROVIDER_OPTIONS.index(st.session_state.transcript["provider"]),
        disabled=config_disabled,
        help="Đổi provider sau khi bắt đầu chat cần tạo cuộc trò chuyện mới.",
    )
    provider = make_provider(provider_name)
    model_override = st.text_input(
        "Model (tuỳ chọn)",
        value="",
        placeholder=provider.default_model,
        disabled=config_disabled,
    )
    version = st.text_input(
        "Version label",
        value=st.session_state.transcript["version"],
        disabled=config_disabled,
    )
    history_window = st.slider("Số lượt lịch sử gửi cho model", 1, 10, 5)
    max_tool_rounds = st.slider("Số vòng gọi tool tối đa", 1, 8, 4)
    st.caption("API keys được đọc từ `.env`; giao diện không hiển thị giá trị key.")
    if config_disabled:
        st.caption("Bấm tạo chat mới để đổi provider, model hoặc version.")
    if st.button("Tạo cuộc trò chuyện mới", use_container_width=True):
        selected_model = model_override.strip() or provider.default_model
        st.session_state.conversation = []
        st.session_state.pending_send = None
        st.session_state.transcript = new_transcript(provider_name, selected_model, version)
        st.rerun()

selected_model = model_override.strip() or provider.default_model
transcript = st.session_state.transcript
if not st.session_state.conversation and (
    transcript["provider"] != provider_name
    or transcript["model"] != selected_model
    or transcript["version"] != version
):
    st.session_state.transcript = new_transcript(provider_name, selected_model, version)

try:
    system_prompt = (ARTIFACTS_DIR / "system_prompt.md").read_text(encoding="utf-8")
    tool_declarations = load_tool_declarations(ARTIFACTS_DIR / "tools.yaml")
    openai_tools = to_openai_tools(tool_declarations)
except (OSError, KeyError, TypeError, ValueError) as exc:
    st.error(f"Không tải được cấu hình agent: {type(exc).__name__}: {exc}")
    st.stop()

for message in st.session_state.conversation:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("tool_events"):
            with st.expander("Chi tiết tool và nguồn"):
                st.json(message["tool_events"])

pending_send = st.session_state.pending_send
if pending_send:
    pending_text = pending_send["text"]
    st.warning("Agent đang đề xuất gửi nội dung dưới đây. Chưa có gì được gửi.")
    st.code(pending_text, language=None)
    confirm_col, cancel_col = st.columns(2)
    if confirm_col.button("Xác nhận gửi", type="primary", key="confirm_send"):
        result = TOOL_FUNCTIONS["send"](text=pending_text, confirmed=True)
        pending_send["event"]["result"] = result
        pending_send["turn"]["external_action_confirmation"] = {
            "confirmed_at": now_iso(),
            "result": result,
        }
        st.session_state.pending_send = None
        save_current_transcript()
        if result.get("status") == "sent":
            st.success("Đã gửi lên Telegram.")
        else:
            st.error(f"Gửi không thành công: {json_text(result)}")
        st.rerun()
    if cancel_col.button("Huỷ, không gửi", key="cancel_send"):
        pending_send["event"]["result"] = {
            "status": "cancelled",
            "message": "User cancelled the Telegram send in the UI.",
        }
        pending_send["turn"]["external_action_confirmation"] = {
            "cancelled_at": now_iso(),
        }
        st.session_state.pending_send = None
        save_current_transcript()
        st.info("Đã huỷ; không có nội dung nào được gửi.")
        st.rerun()

prompt = st.chat_input("Bạn muốn nghiên cứu điều gì?")
if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)

    prior_history = [
        {"role": item["role"], "content": item["content"]}
        for item in st.session_state.conversation
    ]
    messages = [
        {"role": "system", "content": system_prompt},
        *trim_history(prior_history, history_window),
        {"role": "user", "content": prompt},
    ]
    started_at = now_iso()
    turn: dict[str, Any] = {
        "turn_index": len(st.session_state.transcript["turns"]) + 1,
        "started_at": started_at,
        "provider": provider_name,
        "model": selected_model,
        "version": version,
        "user": prompt,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }

    with st.chat_message("assistant"):
        with st.spinner("Đang nghiên cứu..."):
            try:
                result = run_model_tool_loop(
                    provider=provider,
                    messages=messages,
                    tools=openai_tools,
                    model=model_override.strip() or None,
                    max_tool_rounds=max_tool_rounds,
                    tool_executor=ui_tool_executor,
                )
                turn.update(result)
                answer = result["assistant_text"]
                st.markdown(answer)
                pending_event = get_pending_send(result["tool_events"])
                if pending_event:
                    st.warning("Chưa gửi gì cả. Hãy xem nội dung và xác nhận riêng bên dưới nếu muốn gửi.")
                    st.session_state.pending_send = {
                        "text": pending_event["args"].get("text", ""),
                        "event": pending_event,
                        "turn": turn,
                    }
                if result["tool_events"]:
                    with st.expander("Chi tiết tool và nguồn"):
                        st.json(result["tool_events"])
                st.session_state.conversation.extend([
                    {"role": "user", "content": prompt},
                    {
                        "role": "assistant",
                        "content": answer,
                        "tool_events": result["tool_events"],
                    },
                ])
            except Exception as exc:
                error_message = f"{type(exc).__name__}: {exc}"
                turn.update({"status": "provider_error", "error": error_message})
                st.error(f"Không thể hoàn thành yêu cầu: {error_message}")
                st.session_state.conversation.extend([
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": f"Lỗi khi gọi provider: {error_message}"},
                ])

    turn["ended_at"] = now_iso()
    st.session_state.transcript["turns"].append(turn)
    transcript_path = save_current_transcript()
    st.caption(f"Transcript được lưu tại `{transcript_path.relative_to(ROOT)}`.")

if st.session_state.transcript["turns"]:
    transcript_json = json.dumps(st.session_state.transcript, ensure_ascii=False, indent=2)
    st.download_button(
        "Tải transcript JSON",
        data=transcript_json,
        file_name=f"{st.session_state.transcript['transcript_id']}.transcript.json",
        mime="application/json",
    )
