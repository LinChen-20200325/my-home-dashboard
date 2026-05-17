"""Chapter 1：首頁與個人現金流診斷 — Thin wrapper（重構後）。

實作已搬遷至 ``app.ui.pages.chapter_1_cashflow``；本檔保留為 thin wrapper，
讓 ``main.py`` 與其他既有呼叫端的 ``from chapter_1 import render_chapter_1`` 不必變更。

Migration step: Phase 2 #15
"""

from __future__ import annotations

from app.ui.pages.chapter_1_cashflow import render_chapter_1

__all__ = ["render_chapter_1"]


if __name__ == "__main__":
    import streamlit as st

    st.set_page_config(
        page_title="Ch.1 財富思維與現金流診斷",
        page_icon="🏠",
        layout="wide",
    )
    render_chapter_1()
