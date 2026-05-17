"""Unit tests — app.repositories.openai_client（OpenAI 串流包裝）。

不仰賴實際 OpenAI SDK：
    - `_yield_content_chunks` 用 SimpleNamespace 模擬 chunk shape，純函式可測
    - `stream_chat_completion` 對 ImportError 翻譯為 RuntimeError 的測試，
      用 sys.meta_path 真的封鎖 openai import
"""

from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from app.models.ai import AIConfig, ChatMessage, ChatRole
from app.repositories.openai_client import (
    _yield_content_chunks,
    stream_chat_completion,
)


pytestmark = [pytest.mark.repositories]


# ============================================================
# _yield_content_chunks — chunk 解析純函式
# ============================================================
def _chunk(content):
    """產生一個 mock chunk，shape 對齊 openai.ChatCompletionChunk。"""
    return SimpleNamespace(
        choices=[SimpleNamespace(delta=SimpleNamespace(content=content))]
    )


class TestYieldContentChunks:
    def test_standard_chunks_join_to_full_message(self) -> None:
        stream = iter([_chunk("Hello"), _chunk(", "), _chunk("world!")])
        result = list(_yield_content_chunks(stream))
        assert "".join(result) == "Hello, world!"

    def test_none_content_filtered(self) -> None:
        """OpenAI 的 finish-reason chunks 通常 content=None，不該 yield。"""
        stream = iter([_chunk("ok"), _chunk(None), _chunk(" hi")])
        assert list(_yield_content_chunks(stream)) == ["ok", " hi"]

    def test_empty_string_content_filtered(self) -> None:
        """空字串視為 falsy，跟 None 一樣被過濾。"""
        stream = iter([_chunk("a"), _chunk(""), _chunk("b")])
        assert list(_yield_content_chunks(stream)) == ["a", "b"]

    def test_empty_choices_list_skipped(self) -> None:
        """choices=[] 觸發 IndexError，應靜默略過。"""
        empty = SimpleNamespace(choices=[])
        stream = iter([empty, _chunk("after")])
        assert list(_yield_content_chunks(stream)) == ["after"]

    def test_delta_none_skipped(self) -> None:
        """delta=None 觸發 AttributeError，應靜默略過。"""
        no_delta = SimpleNamespace(choices=[SimpleNamespace(delta=None)])
        stream = iter([no_delta, _chunk("after")])
        assert list(_yield_content_chunks(stream)) == ["after"]

    def test_empty_stream(self) -> None:
        assert list(_yield_content_chunks(iter([]))) == []


# ============================================================
# stream_chat_completion — ImportError → RuntimeError 翻譯
# ============================================================
class _OpenAIBlocker:
    """sys.meta_path 攔截器：禁止 `import openai`，模擬未安裝環境。"""

    def find_module(self, name, path=None):  # type: ignore[no-untyped-def]
        if name == "openai" or name.startswith("openai."):
            return self
        return None

    def load_module(self, name):  # type: ignore[no-untyped-def]
        raise ImportError(f"mocked: {name} not installed")


@pytest.fixture
def block_openai():
    """暫時讓 openai 套件變成『未安裝』狀態。"""
    saved_modules = {
        k: sys.modules.pop(k) for k in list(sys.modules)
        if k == "openai" or k.startswith("openai.")
    }
    blocker = _OpenAIBlocker()
    sys.meta_path.insert(0, blocker)
    try:
        yield
    finally:
        sys.meta_path.remove(blocker)
        sys.modules.update(saved_modules)


class TestStreamChatCompletionImportError:
    @pytest.mark.boundary
    def test_missing_openai_raises_runtime_error_with_hint(
        self, block_openai,
    ) -> None:
        """openai 套件未安裝 → 翻譯為 RuntimeError + 友善安裝指引。"""
        cfg = AIConfig(api_key="sk-test")
        gen = stream_chat_completion(cfg, [ChatMessage(ChatRole.USER, "hi")])
        with pytest.raises(RuntimeError) as exc_info:
            next(gen)
        assert "openai" in str(exc_info.value).lower()
        # 確保是 chained from ImportError
        assert isinstance(exc_info.value.__cause__, ImportError)
