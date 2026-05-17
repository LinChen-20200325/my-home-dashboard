"""Strategy Macro：總體經濟與房價燃料理論 — Thin wrapper（重構後）。

實作已搬遷至 ``app.ui.pages.strategy_macro``。
Migration step: Phase 2 #26
"""

from __future__ import annotations

from app.ui.pages.strategy_macro import render_strategy_macro

__all__ = ["render_strategy_macro"]


if __name__ == "__main__":
    import streamlit as st

    st.set_page_config(
        page_title="總體經濟與房價燃料理論",
        page_icon="🌏",
        layout="wide",
    )
    render_strategy_macro()
