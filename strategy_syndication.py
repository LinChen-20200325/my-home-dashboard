"""Strategy Syndication：合資套利與科目四無限槓桿 — Thin wrapper（重構後）。

實作已搬遷至 ``app.ui.pages.strategy_syndication``。
Migration step: Phase 2 #28
"""

from __future__ import annotations

from app.ui.pages.strategy_syndication import render_strategy_syndication

__all__ = ["render_strategy_syndication"]


if __name__ == "__main__":
    import streamlit as st

    st.set_page_config(
        page_title="合資套利與科目四無限槓桿",
        page_icon="🤝",
        layout="wide",
    )
    render_strategy_syndication()
