"""側邊欄路由：CHAPTERS dict + 分派器。

由 ``app/main.py`` composition root 呼叫 ``run()`` 啟動整個 APP。

直接 import 新分層的 ``app.ui.pages.*``（不經過根目錄 thin wrappers），
讓 router 成為架構藍圖的『唯一』正確 entry point。
"""

from __future__ import annotations

from typing import Callable

import streamlit as st

from app.ui.pages.chapter_1_cashflow import render_chapter_1
from app.ui.pages.chapter_2_presale import render_chapter_2
from app.ui.pages.chapter_3_rental import render_chapter_3
from app.ui.pages.chapter_4_refinance import render_chapter_4
from app.ui.pages.chapter_5_resale import render_chapter_5
from app.ui.pages.chapter_6_tax import render_chapter_6
from app.ui.pages.chapter_7_exit import render_chapter_7
from app.ui.pages.chapter_8_advanced import render_chapter_8
from app.ui.pages.chapter_9_ai import render_chapter_9_ai
from app.ui.pages.chapter_10_decision import render_chapter_10_decision_engine
from app.ui.pages.chapter_11_combat import render_chapter_11_combat_manual
from app.ui.pages.strategy_macro import render_strategy_macro
from app.ui.pages.strategy_negotiation import render_strategy_negotiation
from app.ui.pages.strategy_syndication import render_strategy_syndication


# ===== 章節對照表（標籤 → 渲染函式）=====
# 透過 emoji 前綴在視覺上分組：核心章節 / 進階策略
CHAPTERS: dict[str, Callable[[], None]] = {
    # ----- 核心章節（按 Ch.1 → Ch.11 順序）-----
    "🏠 Ch.1 首頁與個人現金流診斷": render_chapter_1,
    "🏗️ Ch.2 預售屋：買就賺選址與合約快篩": render_chapter_2,
    "💰 Ch.3 租金精算與優質租客雷達": render_chapter_3,
    "🏦 Ch.4 槓桿魔法:科目四金流過水 SOP": render_chapter_4,
    "🏢 Ch.5 中古屋：居住成本與出價沙盤推演": render_chapter_5,
    "🛡️ Ch.6 節稅護城河與裝潢抵稅清單": render_chapter_6,
    "🚪 Ch.7 安全離場與流動性評估": render_chapter_7,
    "🔥 Ch.8 奈米級防坑與核彈策略": render_chapter_8,
    "🎓 Ch.9 學長 AI 實戰顧問": render_chapter_9_ai,
    "🧭 Ch.10 400 題極限防坑與決策雷達": render_chapter_10_decision_engine,
    "⚔️ Ch.11 看房現場實戰戰術手冊": render_chapter_11_combat_manual,
    # ----- 進階實戰策略 -----
    "🌏 進階 ｜ 總體經濟與房價燃料理論": render_strategy_macro,
    "💼 進階 ｜ 極限議價與談判心理戰": render_strategy_negotiation,
    "🤝 進階 ｜ 合資套利與科目四無限槓桿": render_strategy_syndication,
}


SIDEBAR_TITLE: str = "📚 房產攻略"
SIDEBAR_CAPTION_TOP: str = "八大核心章節 × 進階策略 × AI 顧問"
SIDEBAR_CAPTION_BOTTOM: str = "v2.1 ｜ 分層架構完整版"


def run() -> None:
    """渲染側邊欄並分派到使用者選擇的頁面。

    呼叫端（``app/main.py`` 或根目錄 ``main.py``）只需要先做完
    ``st.set_page_config(...)``，然後呼叫本函式即可。
    """
    with st.sidebar:
        st.title(SIDEBAR_TITLE)
        st.caption(SIDEBAR_CAPTION_TOP)
        st.markdown("---")
        selected = st.radio(
            "選擇章節",
            list(CHAPTERS.keys()),
            index=0,
            label_visibility="collapsed",
        )
        st.markdown("---")
        st.caption(SIDEBAR_CAPTION_BOTTOM)

    CHAPTERS[selected]()
