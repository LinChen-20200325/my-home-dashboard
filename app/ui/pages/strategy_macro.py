"""Strategy Macro UI — 總體經濟與房價燃料理論（重構後）。

UI 層：純 widgets + 渲染；M2 四象限判定 + 區域紅利評級由 services.leverage。
"""

from __future__ import annotations

import streamlit as st

from app.services.leverage import (
    M2Regime,
    RegionalGrade,
    diagnose_m2_regime,
    diagnose_regional_tailwinds,
)


# ===== UI labels =====
CB_STANCE_OPTIONS: list[str] = [
    "🟢 是 — 央行正在降息 / QE 印鈔（寬鬆）",
    "🔴 否 — 央行正在升息 / 縮表（緊縮）",
]

REGIONAL_TAILWINDS: list[tuple[str, str, str]] = [
    (
        "🚆 區域內有**即將完工**的捷運／高鐵／新幹線站點（軌道紅利）",
        "macro_tw_transit",
        "**軌道經濟學**：通車前 12-18 個月房價開始反映；通車當天 → 出現第一波買盤；"
        "通車滿 1 年 → 租金漲 15-25%。",
    ),
    (
        "🏭 區域內有**指標科學園區 / 大型商辦**進駐（如台積電、半導體 S 廊帶）",
        "macro_tw_tech_hub",
        "**科技人口剛需**：高薪工程師湧入 → 推升租金天花板 + 自住買盤；"
        "**台積電一座廠約創造 10,000 個直接間接職缺**，租金至少漲 30%。",
    ),
    (
        "🏗️ 區域內有**大型指標建商**正在推『**高價預售屋**』",
        "macro_tw_presale_anchor",
        "**比價效應**：預售屋定錨價會帶動中古屋價格——"
        "因為買方會比較『新案 vs 中古』總價，**整區水位被預售屋墊高 15-25%**。",
    ),
]

# Regional grade UI tables (對應 RegionalGrade enum 0-3)
_GRADE_LABELS = ["🔴 普通區", "🟠 一般潛力", "🟢 強勢", "🔥 核彈級"]
_GRADE_PRICE_RANGE = ["≤ 10%", "10-20%", "20-35%", "30-50%"]


def _render_fuel_observation() -> None:
    st.markdown("### ⛽ 區塊一：大盤資金燃料觀測")
    st.caption("學長心法：『**房價的燃料是 M1B，不是基本面**。看懂貨幣，你就看懂下一波。』")

    st.info(
        "📚 **背景知識**：\n"
        "- **M1B** = 現金 + 活期存款 + 活儲（**準備隨時投入市場的熱錢**）\n"
        "- **M2** = M1B + 定存 + 外匯存款（**停泊在安全帳戶的冷錢**）\n"
        "- **M1B 年增率 > M2 年增率 → 黃金交叉**（錢從定存撤出，往股市房市流）\n"
        "- **M1B 年增率 < M2 年增率 → 死亡交叉**（錢回流定存避險）"
    )

    col_a, col_b = st.columns(2)
    with col_a:
        m1b_yoy = st.number_input(
            "📈 M1B 年增率（%）", min_value=-10.0, max_value=30.0, value=8.0,
            step=0.1, format="%.1f",
            help="可上央行『金融統計月報』或財經新聞查詢最新數據。",
            key="macro_m1b",
        )
    with col_b:
        m2_yoy = st.number_input(
            "📊 M2 年增率（%）", min_value=-10.0, max_value=30.0, value=6.0,
            step=0.1, format="%.1f",
            help="長期平均約 5-7%，是台灣房價的『**燃料底氣**』。",
            key="macro_m2",
        )

    cb_stance = st.radio(
        "🏦 央行目前貨幣立場", options=CB_STANCE_OPTIONS, index=0, key="macro_cb_stance",
    )
    is_easing = cb_stance.startswith("🟢")

    regime = diagnose_m2_regime(m1b_yoy, m2_yoy, is_easing)
    gap = regime.gap_pp

    st.markdown("---")
    st.markdown("##### 📊 燃料指標拆解")
    m1, m2, m3 = st.columns(3)
    m1.metric(
        "M1B − M2 差距", f"{gap:+.1f} pp",
        delta=("🟢 黃金交叉" if regime.is_golden_cross else "🔴 死亡交叉"),
        delta_color="normal" if regime.is_golden_cross else "inverse",
    )
    m2.metric("資金水位變化", "📈 熱錢上揚" if regime.is_golden_cross else "📉 冷錢避險")
    m3.metric("央行立場", "🟢 寬鬆" if regime.is_easing else "🔴 緊縮")

    st.markdown("---")

    if regime.regime == M2Regime.SURGE:
        st.success(
            "🚀 **資金狂潮來襲！** 黃金交叉 ＋ 央行寬鬆 ＝ **完美的雙引擎啟動**！\n\n"
            "熱錢正在**股市與房市流竄**，這是『閉著眼睛買核心生產資產都能跟著通膨翻倍』的**最佳上車點**。\n\n"
            f"📐 **目前 M1B 比 M2 高 {gap:.1f} pp**——\n"
            "- M1B 越高 → 越多錢『**準備隨時砸進市場**』\n"
            "- 央行降息 → 借錢成本變便宜 → **槓桿放大效益最大**\n\n"
            "👉 **學長動作清單：**\n"
            "1. **立刻找物件！** 不要再等『**等便宜一點**』——資金狂潮期房價只會更貴\n"
            "2. **拉滿槓桿**（在 DTI < 70% 範圍內）——讓通膨幫你還債\n"
            "3. **鎖長年期低利率**（30 年 + 寬限期）——把現在的便宜利息綁死 10 年\n"
            "4. **核心生產資產優先**：捷運站旁、科學園區邊、明星學區內\n\n"
            "**這種行情 5-10 年才出現一次——錯過這次，下次要再等下個降息循環。**"
        )
    elif regime.regime == M2Regime.DRAIN:
        st.warning(
            "⚠️ **資金退潮期** — 死亡交叉 ＋ 央行緊縮 ＝ **雙重收緊**。\n\n"
            f"📐 **目前 M1B 比 M2 低 {-gap:.1f} pp**——\n"
            "錢正在從活儲撤回定存避險，房市買盤動能不足。\n\n"
            "👉 **學長保命清單：**\n"
            "1. **嚴格控制 DTI < 60%**（一般時期 70%，現在更保守）\n"
            "2. **保留至少 6 個月空租準備金** + 6 個月房貸款（**保命底線**）\n"
            "3. **不要再加碼槓桿**——升息每 0.25% 都會吃掉現金流\n"
            "4. **手上物件若 5 年內要脫手，立刻評估賣壓**\n\n"
            "**度過這段黑天鵝期，活下來的人就是下一波贏家。**"
        )
    elif regime.regime == M2Regime.TRANSITION:
        st.info(
            "🟡 **觀望期 — 黃金交叉但央行緊縮**。\n\n"
            "雖然 M1B 上揚（熱錢在動），但央行還在升息／縮表，借錢成本高。\n\n"
            "👉 **學長判斷**：這是**轉折前夕**——\n"
            "- 通常出現在升息循環尾聲，市場提前反映降息預期\n"
            "- 此時可開始『**看物件 + 估鑑價**』，但**先別下訂**\n"
            "- **等央行明確轉向（首次降息）那一刻**再壓資源進場\n\n"
            "**最聰明的買家不是最先進場的人，是『**轉折點當天**進場的人**』。"
        )
    else:  # BUILDUP
        st.info(
            "🟢 **蓄力期 — 死亡交叉但央行寬鬆**。\n\n"
            "央行已寬鬆但 M1B 還沒翻多，代表熱錢還在猶豫、市場仍在低點。\n\n"
            "👉 **學長判斷**：**這是『**撿便宜**』的黃金窗口！**\n"
            "- 此時屋主開價會比較軟、議價空間大\n"
            "- **積極議價**（按 Ch.5 + 進階議價戰術）\n"
            "- 等 M1B 翻多時 → 你的房子已經買在最低點\n\n"
            "**走在熱錢前面的人，才能賺到最大那一段。**"
        )


def _render_regional_scan() -> None:
    st.markdown("### 🎯 區塊二：區域紅利雙引擎掃描")
    st.caption("學長心法：『**地段不會自己漲——是『紅利』推著它漲。**』")

    st.info(
        "🔍 **掃描你目前看中區域的三大紅利**——"
        "**至少要中 2 項**才值得進場，3 項全中是『**核彈級**』機會。"
    )

    triggered: list[bool] = []
    for label, key, knowledge in REGIONAL_TAILWINDS:
        checked = st.checkbox(label, key=key)
        triggered.append(checked)
        with st.expander("📖 學長解釋『為什麼這項是紅利』", expanded=False):
            st.markdown(knowledge)
        st.markdown("")

    verdict = diagnose_regional_tailwinds(tuple(triggered))
    n = verdict.tailwind_count
    total = len(REGIONAL_TAILWINDS)

    st.markdown("---")
    st.markdown("##### 📊 區域紅利強度")
    p1, p2, p3 = st.columns(3)
    p1.metric("紅利命中數", f"{n} / {total}")
    p2.metric("區域評級", _GRADE_LABELS[n])
    p3.metric(
        "預期 5-10 年漲幅", _GRADE_PRICE_RANGE[n],
        help="**僅供參考**——實際漲幅還要看買進價、屋況、總經環境。",
    )
    st.progress(n / total)

    st.markdown("---")
    if verdict.grade == RegionalGrade.NUCLEAR:
        st.success(
            "🔥 **完美地段雙擊！科技人口剛需 ＋ 軌道經濟 ＋ 預售屋比價效應**——\n\n"
            "這區的房價在未來 **5-10 年具備 30%-50% 的翻倍潛力**！\n\n"
            "👉 **請立刻執行『大量看房 SOP』：**\n"
            "1. **一週看 10 間以上**——建立區域行情的『**手感**』\n"
            "2. **三大平台同步看**：591、樂屋、信義（廣告露出不同）\n"
            "3. **每間房都調謄本**（一張 20 元，能救你一輩子）\n"
            "4. **記錄成 Excel**：地址 / 屋齡 / 坪數 / 開價 / 單價 / 屋主開價心態\n"
            "5. **看到第 20 間時**——你會比仲介還懂這區行情，這時才出價\n\n"
            "**核彈級區域的物件越早搶到越好——3-5 年後再買，你要付的就是『紅利已實現後』的天價。**"
        )
    elif verdict.grade == RegionalGrade.STRONG:
        st.success(
            f"🟢 **{n} 項紅利命中——強勢區域**！\n\n"
            "已具備進場條件，但**還缺一項『**核彈引信**』**才會真正爆發。\n\n"
            "👉 **學長建議**：\n"
            "- 仔細評估剩餘那項紅利**何時可能發生**\n"
            "- 若 1-3 年內有機會 → **現在進場搶先卡位**\n"
            "- 若 5 年以上才可能 → **可以再等等**，先看其他區"
        )
    elif verdict.grade == RegionalGrade.POTENTIAL:
        st.warning(
            f"🟠 **{n} 項紅利命中——一般潛力區**。\n\n"
            "單一紅利推動力有限，**漲幅可能跟不上通膨**。\n\n"
            "👉 **學長建議**：除非價格極具吸引力（市價 8 折以下），"
            "否則**換區再看**——好區域永遠在那裡，不急著這一案。"
        )
    else:  # ORDINARY
        st.error(
            "🚫 **三大紅利皆未命中——普通區。**\n\n"
            "這區的房子很可能**只能跟著通膨小漲**，未來 10 年漲幅可能不到 10%——\n"
            "**等於『通膨小贏，槓桿白扛』**。\n\n"
            "👉 **學長動作**：**換區！** "
            "不要因為『便宜』就買普通區——時間成本太高，10 年後你會後悔。"
        )


def render_strategy_macro() -> None:
    """🌏 總體經濟與房價燃料理論（進階策略）— UI 入口。"""
    st.title("🌏 總體經濟與房價燃料理論")
    st.info(
        "💡 **學長的實戰金句**：「**會看房子的是學徒，會看貨幣的才是師父**。\n"
        "房子怎麼漲、為什麼漲，答案不在房子裡——\n"
        "**答案在央行的印鈔機裡。**」"
    )

    _render_fuel_observation()
    st.markdown("---")
    _render_regional_scan()
