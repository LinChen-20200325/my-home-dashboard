"""OpenAI Chat Completions API 包裝（Repository 層）。

職責：
    將外部 `openai` SDK 隔離在本模組；
    UI / Service 透過 ``AIConfig`` + ``list[ChatMessage]`` 介面互動，
    不需要知道 SDK 內部結構或 chunk 形狀。

例外策略：
    - `ImportError`（openai 套件缺失）→ 翻譯為 `RuntimeError`（含安裝指引）
    - 其他 OpenAI 例外（RateLimitError / APIConnectionError / AuthenticationError）
      **直接 propagate**，由 service / UI 層決定如何重試或翻譯

層架構規則：
    本模組屬 repository 層，**允許** import openai SDK，
    但**嚴禁**呼叫任何 streamlit UI 渲染函式。
"""

from __future__ import annotations

from typing import Iterator

from app.models.ai import AIConfig, ChatMessage


def stream_chat_completion(
    config: AIConfig, messages: list[ChatMessage],
) -> Iterator[str]:
    """以串流模式取得 chat completion，逐塊 yield content 字串。

    Args:
        config:   AI 設定（api_key / model / temperature）
        messages: 對話歷史 DTO 序列（包含 system prompt 必須由呼叫端置首）

    Yields:
        OpenAI 回傳的每個 content delta；空字串、None 與結束訊號的 chunk 不會 yield。

    Raises:
        RuntimeError: openai 套件未安裝。
        openai.OpenAIError 及其子類: API 連線 / 認證 / 速率限制等錯誤
            （照原型 propagate，呼叫端可分別 catch）。
    """
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError(
            "openai 套件未安裝；請執行 `pip install openai>=1.0`，"
            "或將 openai>=1.0 加入 requirements.txt 後重啟服務。"
        ) from exc

    client = OpenAI(api_key=config.api_key)
    stream = client.chat.completions.create(
        model=config.model,
        messages=[m.to_openai_dict() for m in messages],
        temperature=config.temperature,
        stream=True,
    )
    yield from _yield_content_chunks(stream)


def _yield_content_chunks(stream: Iterator) -> Iterator[str]:
    """從 OpenAI 串流 iterable 中逐塊抽取 content 字串。

    抽離為獨立函式以便不依賴實際 OpenAI 連線即可單測 chunk 解析邏輯。

    對下列退化 chunk 形狀採『靜默略過』：
        - choices 為空 list（IndexError）
        - choices[0].delta 為 None（AttributeError）
        - delta.content 為 None / 空字串（falsy 過濾）
    """
    for chunk in stream:
        try:
            delta = chunk.choices[0].delta.content
        except (IndexError, AttributeError):
            delta = None
        if delta:
            yield delta
