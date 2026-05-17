"""學長：房產投資實戰攻略神機 — 主應用程式骨架。

八大核心章節 + 進階策略模組 + AI 顧問，皆以獨立 render 函式分離，側邊欄選單分派渲染。
"""

import streamlit as st

from chapter_1 import render_chapter_1
from chapter_2 import render_chapter_2
from chapter_3 import render_chapter_3
from chapter_4 import render_chapter_4
from chapter_5 import render_chapter_5
from chapter_6 import render_chapter_6
from chapter_7 import render_chapter_7
from chapter_8 import render_chapter_8
from chapter_9 import render_chapter_9_ai
from chapter_10 import render_chapter_10_decision_engine
from chapter_11 import render_chapter_11_combat_manual
from strategy_macro import render_strategy_macro
from strategy_negotiation import render_strategy_negotiation
from strategy_syndication import render_strategy_syndication


# ===================== 頁面基本設定 =====================
st.set_page_config(
    page_title="房產攻略",
    page_icon="🏘️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ===================== 章節對照表（標籤 → 渲染函式）=====================
# 透過 emoji 前綴在視覺上分組：📘 核心章節 / 🎯 進階策略 / 🤖 AI
CHAPTERS = {
    # ----- 核心章節（按 Ch.1 → Ch.11 順序）-----
    "🏠 Ch.1 首頁與個人現金流診斷": render_chapter_1,
    "🏗️ Ch.2 預售屋：買就賺選址與合約快篩": render_chapter_2,
    "💰 Ch.3 租金精算與優質租客雷達": render_chapter_3,
    "🏦 Ch.4 槓桿魔法：科目四金流過水 SOP": render_chapter_4,
    "🏢 Ch.5 中古屋:居住成本與出價沙盤推演": render_chapter_5,
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


# ===================== 側邊欄導航 =====================
with st.sidebar:
    st.title("📚 房產攻略")
    st.caption("八大核心章節 × 進階策略 × AI 顧問")
    st.markdown("---")
    selected_chapter = st.radio(
        "選擇章節",
        list(CHAPTERS.keys()),
        index=0,
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.caption("v2.0 ｜ 完整版（含 AI 顧問）")


# ===================== 路由分派：渲染所選頁面 =====================
CHAPTERS[selected_chapter]()
