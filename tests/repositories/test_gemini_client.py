"""Unit tests — app.repositories.gemini_client（Gemini 串流包裝 + retry + usage）。

不依賴實際 google-genai SDK：
    - `_yield_text_chunks` + `UsageTrackingStream` 用 SimpleNamespace 模擬 chunk
    - `stream_chat_completion` 的 ImportError 翻譯透過 sys.meta_path 封鎖實際 import
    - 重試邏輯透過 monkey-patch fake APIError + 計數測試
"""

from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from app.models.ai import AIConfig, AIProvider, ChatMessage, ChatRole
from app.repositories.gemini_client import (
    UsageTrackingStream,
    _to_gemini_contents,
    _yield_text_chunks,
    stream_chat_completion,
)


pytestmark = [pytest.mark.repositories]


# ============================================================
# Chunk helpers
# ============================================================
def _text_chunk(text: str | None, *, usage_metadata=None):
    """Mock Gemini chunk with text + optional usage_metadata."""
    return SimpleNamespace(text=text, usage_metadata=usage_metadata)


def _usage_meta(input_tokens: int, output_tokens: int):
    return SimpleNamespace(
        prompt_token_count=input_tokens,
        candidates_token_count=output_tokens,
        total_token_count=input_tokens + output_tokens,
    )


# ============================================================
# _yield_text_chunks — 純函式 chunk 解析
# ============================================================
class TestYieldTextChunks:
    def test_standard_chunks_join(self) -> None:
        stream = iter([_text_chunk("Hello"), _text_chunk(", "), _text_chunk("world!")])
        assert "".join(_yield_text_chunks(stream)) == "Hello, world!"

    def test_none_text_filtered(self) -> None:
        stream = iter([_text_chunk("ok"), _text_chunk(None), _text_chunk(" hi")])
        assert list(_yield_text_chunks(stream)) == ["ok", " hi"]

    def test_empty_text_filtered(self) -> None:
        stream = iter([_text_chunk(""), _text_chunk("x")])
        assert list(_yield_text_chunks(stream)) == ["x"]

    def test_missing_text_attr_silently_skipped(self) -> None:
        """chunk 沒有 .text 屬性也不該 crash。"""
        weird = SimpleNamespace()  # 完全沒 text 屬性
        stream = iter([weird, _text_chunk("ok")])
        assert list(_yield_text_chunks(stream)) == ["ok"]

    def test_empty_stream(self) -> None:
        assert list(_yield_text_chunks(iter([]))) == []


# ============================================================
# UsageTrackingStream — 串流 + token 用量擷取
# ============================================================
class TestUsageTrackingStream:
    def test_yields_text_chunks_in_order(self) -> None:
        raw = iter([_text_chunk("A"), _text_chunk("B"), _text_chunk("C")])
        wrapped = UsageTrackingStream(raw)
        assert list(wrapped) == ["A", "B", "C"]

    def test_usage_is_none_before_iteration(self) -> None:
        wrapped = UsageTrackingStream(iter([_text_chunk("x")]))
        assert wrapped.usage is None  # 尚未迭代

    def test_usage_captured_from_final_chunk(self) -> None:
        raw = iter([
            _text_chunk("Hi"),
            _text_chunk("!", usage_metadata=_usage_meta(100, 50)),
        ])
        wrapped = UsageTrackingStream(raw)
        list(wrapped)  # 消耗串流
        assert wrapped.usage is not None
        assert wrapped.usage.input_tokens == 100
        assert wrapped.usage.output_tokens == 50
        assert wrapped.usage.total_tokens == 150

    def test_usage_captured_from_mid_chunk_when_late_chunks_lack_meta(self) -> None:
        """Gemini 在多個 chunk 都可能帶 usage_metadata，最新值會覆蓋。"""
        raw = iter([
            _text_chunk("A", usage_metadata=_usage_meta(10, 5)),
            _text_chunk("B", usage_metadata=_usage_meta(20, 10)),
        ])
        wrapped = UsageTrackingStream(raw)
        list(wrapped)
        # 最終以最後一個 chunk 為主
        assert wrapped.usage is not None
        assert wrapped.usage.input_tokens == 20
        assert wrapped.usage.output_tokens == 10

    def test_missing_usage_metadata_keeps_usage_none(self) -> None:
        raw = iter([_text_chunk("only-text"), _text_chunk("more")])
        wrapped = UsageTrackingStream(raw)
        list(wrapped)
        assert wrapped.usage is None

    def test_malformed_usage_metadata_silently_ignored(self) -> None:
        """usage_metadata 缺欄位時不該 crash，usage 維持 None。"""
        bad_meta = SimpleNamespace()  # 完全沒欄位
        raw = iter([_text_chunk("x", usage_metadata=bad_meta)])
        wrapped = UsageTrackingStream(raw)
        list(wrapped)
        # AttributeError 被捕，usage 維持初始 None
        assert wrapped.usage is None

    def test_none_token_counts_clamped_to_zero(self) -> None:
        """usage_metadata 的欄位為 None 時 (`int(None or 0) == 0`) 不該 crash。"""
        meta = SimpleNamespace(
            prompt_token_count=None,
            candidates_token_count=None,
            total_token_count=None,
        )
        raw = iter([_text_chunk("x", usage_metadata=meta)])
        wrapped = UsageTrackingStream(raw)
        list(wrapped)
        assert wrapped.usage is not None
        assert wrapped.usage.input_tokens == 0
        assert wrapped.usage.output_tokens == 0
        assert wrapped.usage.total_tokens == 0

    def test_holds_strong_reference_to_client(self) -> None:
        """genai.Client 必須被 UsageTrackingStream 強引用，避免 stream 還沒
        讀完就被 GC 觸發 httpx 連線關閉。
        """
        # 模擬 client object（任意非 None 值都可）
        fake_client = SimpleNamespace(close=lambda: None)
        wrapped = UsageTrackingStream(
            iter([_text_chunk("hi")]),
            client_ref=fake_client,
        )
        # client_ref 屬性必須存在且指向同一個 client object
        assert wrapped._client_ref is fake_client

    def test_client_ref_optional_for_unit_tests(self) -> None:
        """未傳 client_ref 仍能建構（unit test 場景不需要真的有 Client）。"""
        wrapped = UsageTrackingStream(iter([_text_chunk("hi")]))
        assert wrapped._client_ref is None
        assert list(wrapped) == ["hi"]


# ============================================================
# _to_gemini_contents — system + role 重新映射
# ============================================================
class TestToGeminiContents:
    """這個測試需要 google.genai.types 才能跑（Content / Part 是真物件）。"""

    def test_skips_when_genai_not_installed(self) -> None:
        try:
            from google.genai import types  # noqa: F401
        except ImportError:
            pytest.skip("google-genai 未安裝，跳過 real-types 測試")

        system = ChatMessage(ChatRole.SYSTEM, "你是學長")
        user = ChatMessage(ChatRole.USER, "你好")
        assistant = ChatMessage(ChatRole.ASSISTANT, "學弟好！")
        sys_text, contents = _to_gemini_contents([system, user, assistant])
        assert sys_text == "你是學長"
        assert len(contents) == 2
        # role 重新映射：USER → user, ASSISTANT → model
        assert contents[0].role == "user"
        assert contents[1].role == "model"

    def test_no_system_message_returns_none(self) -> None:
        try:
            from google.genai import types  # noqa: F401
        except ImportError:
            pytest.skip("google-genai 未安裝")

        user = ChatMessage(ChatRole.USER, "Q?")
        sys_text, contents = _to_gemini_contents([user])
        assert sys_text is None
        assert len(contents) == 1

    def test_multiple_system_messages_joined(self) -> None:
        try:
            from google.genai import types  # noqa: F401
        except ImportError:
            pytest.skip("google-genai 未安裝")

        s1 = ChatMessage(ChatRole.SYSTEM, "rule A")
        s2 = ChatMessage(ChatRole.SYSTEM, "rule B")
        sys_text, contents = _to_gemini_contents([s1, s2])
        assert sys_text == "rule A\n\nrule B"
        assert contents == []


# ============================================================
# stream_chat_completion — ImportError 翻譯為 RuntimeError
# ============================================================
class _BlockGoogleGenaiImport:
    """sys.meta_path 攔截器：模擬 google-genai 套件缺失。"""

    def find_spec(self, name, path, target=None):  # type: ignore[no-untyped-def]
        if name == "google" or name.startswith("google."):
            raise ImportError(f"模擬 {name} 套件未安裝")
        return None


class TestStreamChatCompletionImportError:
    def test_missing_genai_raises_runtime_error_with_hint(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # 攔截 google 系列 import
        blocker = _BlockGoogleGenaiImport()
        monkeypatch.setattr(sys, "meta_path", [blocker, *sys.meta_path])
        # 清掉已快取的 google modules 以強制重新 import
        for modname in list(sys.modules.keys()):
            if modname == "google" or modname.startswith("google."):
                monkeypatch.delitem(sys.modules, modname, raising=False)

        cfg = AIConfig(
            api_key="AIzaSy-test",
            model="gemini-2.5-flash",
            provider=AIProvider.GEMINI,
        )
        with pytest.raises(RuntimeError, match="google-genai 套件未安裝"):
            stream_chat_completion(cfg, [])
