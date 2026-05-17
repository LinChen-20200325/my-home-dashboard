"""API Key 雙來源讀取器（Repository 層）。

提供從 Streamlit secrets 與呼叫端 candidate（通常是 sidebar 輸入）
兩個來源解析 API Key 的邏輯。

依層架構規則：
    本模組屬 repository 層，**允許** import streamlit
    （`st.secrets` 是 Streamlit 提供的外部設定存取入口），
    但**嚴禁**呼叫任何 UI 渲染函式（st.title / st.write / st.metric 等）。

懶載入策略：
    streamlit import 用 try/except 包裝，
    讓服務在純 Python / unit test 環境也能直接使用，
    不會因 streamlit 未安裝而 ImportError。
"""

from __future__ import annotations

try:
    import streamlit as _st
    _STREAMLIT_AVAILABLE = True
except ImportError:
    _STREAMLIT_AVAILABLE = False


def read_streamlit_secret(name: str) -> str | None:
    """從 ``st.secrets`` 讀取指定名稱的設定值。

    回傳 None 的情境：
        - streamlit 未安裝
        - secrets.toml 不存在 / 損毀
        - 指定的 key 不存在
        - 值為空字串或全空白

    任何讀取例外都會被吞掉並回傳 None，避免讓上層因 setup 問題崩潰。
    """
    if not _STREAMLIT_AVAILABLE:
        return None
    try:
        # 用 `in` 檢查避免在 key 缺失時拋 StreamlitSecretNotFoundError
        if name in _st.secrets:  # type: ignore[operator]
            value = str(_st.secrets[name]).strip()
            return value or None
    except Exception:
        # secrets.toml 不存在 / 解析錯誤 / 任何 SDK 變動 → 靜默回 None
        pass
    return None


def resolve_api_key(
    sidebar_candidate: str | None, secret_name: str,
) -> str | None:
    """API Key 解析優先序：``st.secrets`` > sidebar candidate。

    回傳第一個『非空且 trim 後仍非空』的字串，或 None。

    Args:
        sidebar_candidate: UI 側邊欄即時輸入的字串（可為 None 或空）。
        secret_name:       在 ``st.secrets`` 中查詢的鍵名（例：``OPENAI_API_KEY``）。

    Returns:
        解析後的 API Key 字串；兩來源都缺則回傳 None。
    """
    from_secret = read_streamlit_secret(secret_name)
    if from_secret:
        return from_secret
    if sidebar_candidate:
        stripped = sidebar_candidate.strip()
        if stripped:
            return stripped
    return None
