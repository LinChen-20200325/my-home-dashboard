"""Google Gemini API 包裝（Repository 層）。

職責：
    將外部 ``google-genai`` SDK 隔離在本模組；
    UI / Service 透過 ``AIConfig`` + ``list[ChatMessage]`` 介面互動，
    與 ``openai_client.py`` 對稱（同樣回傳 ``UsageTrackingStream``）。

例外策略：
    - ``ImportError``（google-genai 套件缺失）→ 翻譯為 ``RuntimeError``（含安裝指引）
    - 速率限制 / 連線層錯誤 → 自動重試（指數退避，最多 ``OPENAI_MAX_RETRIES`` 次，
      共用 OPENAI_* 常數命名以維持設定 SSOT；常數本身非 provider-specific）
    - 其他 SDK 例外 → 直接 propagate

Token 用量追蹤：
    ``UsageTrackingStream`` 在迭代完成後於 ``.usage`` 暴露 ``TokenUsage``，
    對應 Gemini 的 ``usage_metadata.prompt_token_count`` / ``candidates_token_count``。

層架構規則：
    本模組屬 repository 層，**允許** import google-genai SDK，
    但**嚴禁**呼叫任何 streamlit UI 渲染函式。
"""

from __future__ import annotations

import time
from typing import Any, Iterator

from app.models.ai import ChatRole, ChatMessage, AIConfig, TokenUsage
from app.models.constants import OPENAI_MAX_RETRIES, OPENAI_RETRY_BASE_DELAY_SECONDS


class UsageTrackingStream:
    """Gemini 串流的 iterable 包裝，迭代完成後在 ``.usage`` 暴露 token 用量。

    Gemini chunk 形狀：``chunk.text`` 為片段文字；最後一個 chunk 帶
    ``chunk.usage_metadata`` 包含 prompt_token_count / candidates_token_count /
    total_token_count。本 class 在迭代過程中擷取並保留。
    """

    def __init__(self, raw_stream: Iterator[Any]) -> None:
        self._raw = raw_stream
        self._usage: TokenUsage | None = None

    def __iter__(self) -> Iterator[str]:
        for chunk in self._raw:
            text = getattr(chunk, "text", None)
            if text:
                yield text
            # Gemini 在每個 chunk 都可能帶 usage_metadata（最後一個最完整）
            meta = getattr(chunk, "usage_metadata", None)
            if meta is not None:
                try:
                    self._usage = TokenUsage(
                        input_tokens=int(meta.prompt_token_count or 0),
                        output_tokens=int(meta.candidates_token_count or 0),
                        total_tokens=int(meta.total_token_count or 0),
                    )
                except (AttributeError, TypeError):
                    # SDK 變動 / mock object 缺欄位 → 靜默忽略
                    pass

    @property
    def usage(self) -> TokenUsage | None:
        return self._usage


def _to_gemini_contents(messages: list[ChatMessage]) -> tuple[str | None, list[Any]]:
    """把 ChatMessage 序列拆成 (system_instruction, contents)。

    Gemini 的 system instruction 透過 ``GenerateContentConfig`` 注入，
    不混在 contents list 裡；assistant role 在 Gemini 端叫 ``model``。
    """
    # 延後 import 避免 unit test 環境一定要裝 google-genai
    from google.genai import types  # type: ignore[import-not-found]

    system_text: str | None = None
    contents: list[Any] = []
    for msg in messages:
        if msg.role == ChatRole.SYSTEM:
            # 多個 system message → 用換行串起來（學長 persona 目前只有一段）
            system_text = (
                msg.content if system_text is None
                else f"{system_text}\n\n{msg.content}"
            )
            continue
        gemini_role = "user" if msg.role == ChatRole.USER else "model"
        contents.append(
            types.Content(
                role=gemini_role,
                parts=[types.Part.from_text(text=msg.content)],
            )
        )
    return system_text, contents


def stream_chat_completion(
    config: AIConfig, messages: list[ChatMessage],
) -> UsageTrackingStream:
    """以串流模式呼叫 Gemini，回傳可迭代的 ``UsageTrackingStream``。

    Args:
        config:   AI 設定（api_key / model / temperature）。provider 欄位忽略，
                  本函式即代表 Gemini 路徑。
        messages: 對話歷史 DTO 序列；system message 由本函式自動抽出注入
                  ``GenerateContentConfig.system_instruction``。

    Returns:
        ``UsageTrackingStream`` — 迭代會 yield 每個 text chunk；迭代完成後可讀
        ``.usage`` 屬性取得 ``TokenUsage``。

    Raises:
        RuntimeError: google-genai 套件未安裝。
        其他 google.genai 例外: 認證 / 連線 / 速率限制等錯誤（已自動重試
            ``OPENAI_MAX_RETRIES`` 次仍失敗才會 propagate）。
    """
    try:
        from google import genai  # type: ignore[import-not-found]
        from google.genai import types, errors  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "google-genai 套件未安裝；請執行 `pip install google-genai>=1.0`，"
            "或將 google-genai>=1.0 加入 requirements.txt 後重啟服務。"
        ) from exc

    client = genai.Client(api_key=config.api_key)
    system_text, contents = _to_gemini_contents(messages)

    gen_config = types.GenerateContentConfig(
        temperature=config.temperature,
        system_instruction=system_text,
    )

    # Gemini 可重試的錯誤型別：ClientError(429) / ServerError(5xx) / 連線錯誤。
    # 我們撈 errors.APIError 作為 base（涵蓋上述），與 openai 對稱。
    retryable_exc: tuple[type[BaseException], ...] = (
        getattr(errors, "APIError", Exception),
    )

    last_exc: BaseException | None = None
    for attempt in range(OPENAI_MAX_RETRIES + 1):
        try:
            raw_stream = client.models.generate_content_stream(
                model=config.model,
                contents=contents,
                config=gen_config,
            )
            return UsageTrackingStream(raw_stream)
        except retryable_exc as exc:
            last_exc = exc
            if attempt >= OPENAI_MAX_RETRIES:
                raise
            time.sleep(OPENAI_RETRY_BASE_DELAY_SECONDS * (2 ** attempt))

    # 理論上不會到達
    raise RuntimeError("retry loop exited unexpectedly") from last_exc


def _yield_text_chunks(stream: Iterator[Any]) -> Iterator[str]:
    """純函式版本的 chunk 解析（供 unit test 直接呼叫，不需 Gemini 連線）。

    對退化 chunk（無 .text 屬性 / .text 為空）採『靜默略過』。
    """
    for chunk in stream:
        text = getattr(chunk, "text", None)
        if text:
            yield text
