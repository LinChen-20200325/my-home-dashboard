"""Chapter 5 UI — 中古屋投資排雷與議價術（重構後）。

UI 層：純 widgets + 渲染；地雷判定 + SOP 完成度由 services.liquidity 計算。
"""

from __future__ import annotations

import streamlit as st

from app.services.liquidity import (
    NegotiationReadiness,
    diagnose_liquidity_traps,
    diagnose_negotiation_sop,
)


# ===== UI labels（保留原文）=====
LIQUIDITY_TRAPS: list[tuple[str, str, str]] = [
    (
        "① 民國 88 年（1999）九二一大地震**之前**蓋的房子",
        "ch5_trap_pre921",
        "**耐震規範升級前的老建築**——銀行鑑價、貸款年期、保險都吃虧，"
        "都更難度也高。",
    ),
    (
        "② 屋齡 **>40 年**的公寓 **4 樓**或 **5 樓**（俗稱『健身公寓』）",
        "ch5_trap_old_walkup_top",
        "**沒電梯 + 老年化社區**——租客流動慢，老屋主想下車的人越來越多，"
        "你買進去就是接最後一棒。",
    ),
    (
        "③ **山區豪宅**（小黑蚊密集、通勤極不便、坡地擔保品）",
        "ch5_trap_mountain",
        "**銀行鑑價打折最兇**的物件類型，加上小黑蚊讓租客一個月就想退租。",
    ),
    (
        "④ 老舊大樓的 **2 樓**（管線轉折處）或 **頂樓**（漏水酷熱）",
        "ch5_trap_2f_or_top",
        "管線坐廁／頂樓漏水是兩大『**鄰居恩怨製造機**』，未來修繕費恐怖。",
    ),
]

NEGOTIATION_SOP: list[tuple[str, str, str]] = [
    ("**步驟 1**：查樂居實價登錄，**去掉最高、最低價取平均**", "ch5_sop_pricelookup",
     "別被仲介只給你看『最高價』影響——平均值才是真行情。"),
    ("**步驟 2**：花 20 元調閱**第二類謄本**", "ch5_sop_title_deed",
     "謄本看不懂沒關係，但**沒看就出價**等於蒙眼跳火坑。"),
    ("**步驟 3**：確認**土地項目不為空白**（防範地上權住宅）", "ch5_sop_land_check",
     "土地欄空白＝你只買到使用權，**未來房子歸零**。"),
    ("**步驟 4**：查『**他項權利部**』無私人（自然人）設定", "ch5_sop_no_private_lien",
     "私人設定他項權利＝民間高利貸／地下錢莊，**黑道追討會找上新屋主**。"),
    ("**步驟 5**：**逆推屋主剩餘貸款本金**（用買入年份 + 推估貸款）", "ch5_sop_seller_loan",
     "屋主剩多少貸款＝他的『**心理停損點**』——這是你殺價的關鍵情報。"),
    ("**步驟 6**：**設定出價天花板**（絕不超過銀行鑑價）", "ch5_sop_price_ceiling",
     "銀行鑑價就是你的『不會虧』底線——買貴了，自備款會被迫拉高。"),
    ("**步驟 7**：談判桌上**從單價議到總價，最後砍零頭**", "ch5_sop_haggle_tactic",
     "先咬單價（每坪壓 1-2 萬）→ 再轉攻總價 → 最後『**那 8 萬零頭幫我抹掉**』，對方通常會妥協。"),
]

# 8 段準備度等級顯示（對應 0-7 完成步驟數）
_READINESS_LADDER = [
    "🔴 完全沒準備", "🔴 還早", "🟠 太早", "🟡 半套",
    "🟡 還缺", "🟢 接近", "🟢 即將完備", "✅ 滿載",
]


def _render_liquidity_traps() -> None:
    st.markdown("### 💀 區塊一：流動性極度惡劣排雷針")
    st.caption("學長心法：『**買得便宜不算贏，賣得掉才是真贏。**』")

    hits = tuple(st.checkbox(label, key=key) for label, key, _ in LIQUIDITY_TRAPS)
    verdict = diagnose_liquidity_traps(hits)

    if verdict.has_any_trap:
        triggered_lines = [
            f"- {LIQUIDITY_TRAPS[i][0].split('（')[0]}\n  → {LIQUIDITY_TRAPS[i][2]}"
            for i, hit in enumerate(hits) if hit
        ]
        st.error(
            f"🚫 **流動性地雷！踩到 {verdict.trap_count} 項危險特徵：**\n\n"
            + "\n\n".join(triggered_lines)
            + "\n\n---\n\n這類物件的共同問題：\n"
            "- **銀行貸款成數低、年期短**，買方頭期款必須拉高\n"
            "- **未來接手買盤極少**，砍 20% 都未必賣得掉\n"
            "- **租客流動率高**，空租期會吃掉你所有獲利\n\n"
            "👉 **學長判斷：絕對不要碰！** 房地產第一守則是『流動性』——"
            "**買得到不算本事，能脫手才是真本事**。"
        )
    else:
        st.success(
            "✅ 四大流動性地雷皆未踩到，物件基本條件 OK，可進入下一階段：**情報偵查 + 議價**。"
        )


def _render_negotiation_sop() -> None:
    st.markdown("### 🎯 區塊二：情報偵查與議價沙盤推演")
    st.caption("學長心法：『**準備 99% + 出價 1%，才叫真正的買賣。**』")
    st.info(
        "📋 **學長親傳『出價前必做 7 步驟』** — 跳過任何一步，"
        "你就是案場眼中的『盤子（不懂裝懂的肥羊）』。"
    )

    done_flags = tuple(
        st.checkbox(label, key=key, help=hint) for label, key, hint in NEGOTIATION_SOP
    )
    verdict = diagnose_negotiation_sop(done_flags)
    completed = verdict.completed_count
    total = verdict.total_steps

    st.markdown("---")
    st.markdown("##### 📊 出價準備進度")
    p1, p2, p3 = st.columns(3)
    p1.metric("已完成步驟", f"{completed} / {total}")
    p2.metric("準備度等級", _READINESS_LADDER[completed])
    p3.metric(
        "可否出價",
        "✅ GO" if verdict.readiness == NegotiationReadiness.READY else "❌ 等等",
        delta_color="off",
    )
    st.progress(completed / total)

    st.markdown("---")
    if verdict.readiness == NegotiationReadiness.READY:
        st.success(
            "🚀 **7 步驟全部到位！** 現在你才是『**有準備的買家**』。\n\n"
            "👉 **學長進場順序：**\n"
            "1. 先丟一個比天花板再低 10% 的『試水溫價』\n"
            "2. 等仲介殺價回來，咬住單價不放\n"
            "3. 卡到屋主『剩餘貸款本金 + 5%』附近成交（這是他的真正停損點）\n"
            "4. 最後零頭一定要砍——**請仲介自己想辦法吸收**"
        )
    elif verdict.readiness == NegotiationReadiness.INCOMPLETE:
        st.warning(
            f"🟡 已完成 {completed} / {total} 步，**還缺 {total - completed} 步就要出價？**\n\n"
            "這 7 步缺一不可——尤其是**謄本沒查、剩餘本金沒推**就出價，等於送錢給屋主。"
        )
    else:
        st.error(
            f"🚫 **準備度太低（{completed} / {total}）！** "
            "現在出價就是『**盤子**』。學長攔住你：先把功課做完再說。"
        )


def render_chapter_5() -> None:
    """🏢 中古屋：居住成本與出價沙盤推演（Chapter 5）— UI 入口。"""
    st.title("🏢 中古屋：居住成本與出價沙盤推演")
    st.info(
        "💡 **學長的實戰金句**：「**實價登錄是給你看『他賣多少』，不是『你該出多少』。**\n"
        "出價要往下砍、不要往上追；屋主開的是『心願價』，你要還的是『成交價』。」"
    )

    _render_liquidity_traps()
    st.markdown("---")
    _render_negotiation_sop()
