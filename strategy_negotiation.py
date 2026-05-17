"""Strategy Negotiation：極限議價與談判心理戰 — Thin wrapper（重構後）。

實作已搬遷至 ``app.ui.pages.strategy_negotiation``。
Migration step: Phase 2 #27
"""

from __future__ import annotations

from app.ui.pages.strategy_negotiation import render_strategy_negotiation

__all__ = ["render_strategy_negotiation"]


if __name__ == "__main__":
    import streamlit as st

    st.set_page_config(
        page_title="極限議價與談判心理戰",
        page_icon="💼",
        layout="wide",
    )
    render_strategy_negotiation()
