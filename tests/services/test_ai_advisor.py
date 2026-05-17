"""Unit tests — app.services.ai_advisor（對話編排 + persona prompt）。

ai_advisor 不直接接 OpenAI SDK；OpenAI 互動由 repositories.openai_client 負責。
本測試模組 monkey-patch `stream_chat_completion` 把整個 SDK 鏈路切斷，
專注驗證 service 自己的編排邏輯。
"""

from __future__ import annotations

import pytest

from app.models.ai import AIConfig, ChatMessage, ChatRole
from app.services import ai_advisor
from app.services.ai_advisor import (
    MENTOR_SYSTEM_PROMPT,
    build_message_chain,
    stream_mentor_reply,
)


pytestmark = [pytest.mark.services]


# ============================================================
# build_message_chain — 純函式 prepend SYSTEM
# ============================================================
class TestBuildMessageChain:
    def test_empty_history_yields_system_only(self) -> None:
        chain = build_message_chain([])
        assert len(chain) == 1
        assert chain[0].role == ChatRole.SYSTEM
        assert chain[0].content == MENTOR_SYSTEM_PROMPT

    def test_with_history_preserves_order(self) -> None:
        u1 = ChatMessage(ChatRole.USER, "學長，DTI 60% 可以買嗎？")
        a1 = ChatMessage(ChatRole.ASSISTANT, "可以，但要看你的壞債佔比。")
        u2 = ChatMessage(ChatRole.USER, "我有 2 萬車貸。")
        chain = build_message_chain([u1, a1, u2])
        assert len(chain) == 4
        assert chain[0].role == ChatRole.SYSTEM
        assert chain[1] is u1
        assert chain[2] is a1
        assert chain[3] is u2

    def test_does_not_mutate_caller_list(self) -> None:
        """frozen dataclass + 新 list 回傳 — caller history 不該被改。"""
        history = [ChatMessage(ChatRole.USER, "hello")]
        original_id = id(history)
        original_len = len(history)
        build_message_chain(history)
        assert id(history) == original_id
        assert len(history) == original_len


# ============================================================
# MENTOR_SYSTEM_PROMPT — 內容守則
# ============================================================
class TestMentorSystemPrompt:
    def test_prompt_is_nonempty(self) -> None:
        assert len(MENTOR_SYSTEM_PROMPT) > 500

    @pytest.mark.parametrize(
        "keyword",
        ["學長", "DTI", "履約保證", "M2", "科目四", "學弟"],
    )
    def test_contains_core_keywords(self, keyword: str) -> None:
        """系統提示語必須提到核心 persona / 鐵律字眼。"""
        assert keyword in MENTOR_SYSTEM_PROMPT


# ============================================================
# stream_mentor_reply — 串流委派（mock OpenAI）
# ============================================================
class TestStreamMentorReply:
    def test_is_generator(self) -> None:
        cfg = AIConfig(api_key="sk-test")
        gen = stream_mentor_reply(cfg, [])
        assert hasattr(gen, "__iter__") and hasattr(gen, "__next__")

    def test_generator_creation_is_lazy(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """建立 generator 不該立刻呼叫 OpenAI（lazy evaluation）。"""
        called: list[bool] = []

        def fake_stream(config, messages):  # type: ignore[no-untyped-def]
            called.append(True)
            yield "x"

        monkeypatch.setattr(ai_advisor, "stream_chat_completion", fake_stream)
        gen = stream_mentor_reply(AIConfig(api_key="sk-test"), [])
        assert called == []  # 未消費 generator 前不該觸發
        next(gen)
        assert called == [True]

    def test_yields_chunks_from_repository(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """確認 yield 的內容來自 repository.stream_chat_completion。"""
        captured_chain: list[ChatMessage] = []

        def fake_stream(config, messages):  # type: ignore[no-untyped-def]
            captured_chain.extend(messages)
            yield "Hello"
            yield ", "
            yield "world!"

        monkeypatch.setattr(ai_advisor, "stream_chat_completion", fake_stream)
        cfg = AIConfig(api_key="sk-test")
        user_msg = ChatMessage(ChatRole.USER, "test")
        result = list(stream_mentor_reply(cfg, [user_msg]))
        assert result == ["Hello", ", ", "world!"]
        # repository 收到的 messages 應該是 [SYSTEM, USER]
        assert len(captured_chain) == 2
        assert captured_chain[0].role == ChatRole.SYSTEM
        assert captured_chain[1] == user_msg

    def test_passes_config_through(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """AIConfig 原型傳遞給 repository（model / temperature / api_key）。"""
        seen_configs: list[AIConfig] = []

        def fake_stream(config, messages):  # type: ignore[no-untyped-def]
            seen_configs.append(config)
            yield ""

        monkeypatch.setattr(ai_advisor, "stream_chat_completion", fake_stream)
        cfg = AIConfig(api_key="sk-test", model="gpt-4o", temperature=0.3)
        list(stream_mentor_reply(cfg, []))
        assert len(seen_configs) == 1
        assert seen_configs[0] is cfg

    def test_exception_propagates(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """repository 拋的例外應該原型 propagate（不該被 service 吞掉）。"""
        class FakeRateLimitError(Exception):
            pass

        def fake_stream(config, messages):  # type: ignore[no-untyped-def]
            raise FakeRateLimitError("rate limit hit")
            yield  # pragma: no cover  (生成器需要 yield 才算 generator)

        monkeypatch.setattr(ai_advisor, "stream_chat_completion", fake_stream)
        with pytest.raises(FakeRateLimitError, match="rate limit"):
            list(stream_mentor_reply(AIConfig(api_key="sk-test"), []))
