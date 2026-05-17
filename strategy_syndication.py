"""進階策略模組：學長 — 合資套利與科目四無限槓桿

獨立模組：提供 render_strategy_syndication() 函式。

    from strategy_syndication import render_strategy_syndication
    render_strategy_syndication()
"""

import streamlit as st


# ===== 套利公式核心參數 =====
CASH_DEAL_DEFAULT_DISCOUNT = 0.80      # 現金買斷預設為市價 8 折
BANK_REVAL_LTV = 0.80                  # 半年後重新鑑價可增貸 80%
WAIT_MONTHS_FOR_REVAL = 6              # 銀行重新鑑價門檻（月）

# ===== 合資產權四道防護鎖 =====
SYNDICATION_SAFEGUARDS: list[tuple[str, str, str]] = [
    (
        "① 股東人數設定為**奇數**（3、5、7 人）",
        "syn_safeguard_odd_shareholders",
        "**為什麼？** 投票表決時奇數能避免 50% vs 50% 的『死局』——"
        "**沒有奇數，最後一定鬧上法院僵持不下**。",
    ),
    (
        "② 已設定**二順位抵押權登記**（其他股東聯合設定）",
        "syn_safeguard_second_lien",
        "**為什麼？** 房子登記在某股東名下，**他若個人欠債被法拍**，"
        "其他股東的錢就跟著陪葬。二順位抵押權設定後，"
        "**債權人查封前你們有優先受償權**。",
    ),
    (
        "③ 已設定**預告登記**（地政事務所申請）",
        "syn_safeguard_pre_registration",
        "**為什麼？** 登記名義人若**偷偷過戶捲款落跑**，"
        "預告登記會讓任何變動**必須得到其他股東同意**才能完成。"
        "**這是防止『內賊』的最後一道閘門**。",
    ),
    (
        "④ 退場機制寫死『**僅退 8 折**』或『**12 個月分期退回**』",
        "syn_safeguard_exit_clause",
        "**為什麼？** 沒有退場違約條款，**某股東一鬧情緒要退股**，"
        "其他人必須馬上湊一大筆錢——**直接資金斷鏈**。\n"
        "寫死 8 折或分期，是**逼想退場的人理性思考成本**。",
    ),
]


def _render_arbitrage_tab() -> None:
    """分頁一：合資無本套利推演"""
    st.subheader("💰 合資無本套利推演")
    st.caption("學長心法：『**集資 → 砸破盤 → 增貸 → 抽本金 → 0 成本收租**』")

    col_a, col_b = st.columns(2)
    with col_a:
        market_price_wan = st.number_input(
            "🏠 目標物件市價（萬）",
            min_value=0.0,
            value=2_000.0,
            step=10.0,
            format="%.1f",
            help="實價登錄合理行情，銀行半年後也是以這個基準鑑價。",
            key="syn_arb_market_price",
        )
    with col_b:
        default_cash_deal = round(market_price_wan * CASH_DEAL_DEFAULT_DISCOUNT, 1)
        cash_deal_wan = st.number_input(
            "💵 現金買斷談判價（萬）",
            min_value=0.0,
            value=default_cash_deal,
            step=10.0,
            format="%.1f",
            help=f"預設為市價 {CASH_DEAL_DEFAULT_DISCOUNT * 100:.0f} 折——這是學長的『破盤目標』。"
            "屋主急脫手時才可能接受。",
            key="syn_arb_cash_deal",
        )

    renovation_cost_wan = st.number_input(
        "🔨 預估輕裝修成本（萬）",
        min_value=0.0,
        value=80.0,
        step=10.0,
        format="%.1f",
        help="基本油漆、清潔、廚衛局部更新，**抬高銀行鑑價**用。",
        key="syn_arb_renovation",
    )

    # ---------- 學長公式核心計算 ----------
    bank_reval_wan = market_price_wan              # 半年後重新鑑價 = 回歸市價
    refinanced_wan = bank_reval_wan * BANK_REVAL_LTV  # 可增貸金額
    net_arbitrage_wan = refinanced_wan - cash_deal_wan - renovation_cost_wan

    st.markdown("---")
    st.markdown(f"##### 📊 學長套利公式拆解（{WAIT_MONTHS_FOR_REVAL} 個月後）")

    m1, m2, m3 = st.columns(3)
    m1.metric(
        f"{WAIT_MONTHS_FOR_REVAL} 個月後銀行鑑價",
        f"{bank_reval_wan:,.1f} 萬",
        delta=f"+{(bank_reval_wan - cash_deal_wan):,.1f} 萬 vs 你的買價",
        help="銀行半年後重估，會回歸市價而非你買到的破盤價。",
    )
    m2.metric(
        f"可增貸金額（鑑價 × {BANK_REVAL_LTV * 100:.0f}%）",
        f"{refinanced_wan:,.1f} 萬",
        help="第二次貸款向銀行『把現金搬出來』的天花板。",
    )
    m3.metric(
        "🔨 裝修成本",
        f"{renovation_cost_wan:,.1f} 萬",
        delta_color="inverse",
    )

    st.markdown("---")
    delta_label = (
        f"vs 投入 {cash_deal_wan + renovation_cost_wan:,.1f} 萬"
    )
    st.metric(
        "🎯 預估『拿回本金 + 額外套出的現金』",
        f"{net_arbitrage_wan:,.1f} 萬",
        delta=delta_label,
        delta_color="normal" if net_arbitrage_wan >= 0 else "inverse",
        help="增貸搬出的錢 − 現金買斷成本 − 裝修費。",
    )

    if net_arbitrage_wan > 0:
        st.info(
            "💡 **這就是富人的魔法！**\n\n"
            "**操作流程拆解：**\n"
            f"1. 合資股東集資 **{cash_deal_wan:,.1f} 萬現金**，"
            "全款砸出破盤價拿下房子\n"
            f"2. 投入 **{renovation_cost_wan:,.1f} 萬裝修費**，"
            "讓房子看起來『**有人住、會升值**』\n"
            f"3. 出租 **{WAIT_MONTHS_FOR_REVAL} 個月**累積房客 + 租金紀錄\n"
            f"4. {WAIT_MONTHS_FOR_REVAL} 個月後向銀行申請增貸——"
            f"鑑價回到 **{bank_reval_wan:,.1f} 萬**，可貸出 **{refinanced_wan:,.1f} 萬**\n"
            f"5. **本金 + 裝修費全數抽回**，還多套出 **{net_arbitrage_wan:,.1f} 萬**！\n\n"
            "**最終結果：股東們 0 成本擁有一間正現金流的收租房！**\n"
            "**這就是為什麼有錢人越來越有錢——他們用銀行的錢買資產，"
            "讓房客幫他們還貸。**"
        )
    else:
        st.error(
            f"❌ **這筆生意不划算！** 淨套利 **{net_arbitrage_wan:,.1f} 萬**（負）。\n\n"
            "原因可能是：\n"
            "- 現金談判價砍得不夠深（學長標準：市價 8 折以下）\n"
            "- 裝修預算過高，吃掉增貸利潤\n"
            "- 銀行 LTV 假設過樂觀\n\n"
            "👉 **學長建議**：把目標買價再壓低，或換物件——**不賺不做**。"
        )

    st.markdown("---")
    st.warning(
        "⚠️ **學長警告**：這套操作的前提是——\n\n"
        "1. **股東之間 100% 信任**（建議親兄弟姊妹 / 多年戰友）\n"
        "2. **嚴格走科目四金流過水 SOP**（請參考 Ch.4）\n"
        "3. **產權必須上四道防護鎖**（請看下一頁！）\n\n"
        "**少一條，最後不是套利，是上法院。**"
    )


def _render_safeguard_tab() -> None:
    """分頁二：合資產權絕對防護鎖"""
    st.subheader("🔐 合資產權絕對防護鎖")
    st.caption("學長心法：『**合資前是兄弟，分錢時是仇人——**法律文件是唯一解藥。』")

    st.info(
        "📚 **背景知識**：房子只能登記在『**一個人**』名下，但出錢的是好幾個股東。\n"
        "沒有以下四道法律防護鎖，**登記人隨時可以背叛全體**——"
        "九成的合資糾紛都是因為缺了這幾道鎖。"
    )

    st.markdown("---")
    triggered_missing: list[str] = []
    for label, key, reason in SYNDICATION_SAFEGUARDS:
        checked = st.checkbox(label, key=key)
        with st.expander("📖 為什麼這道鎖必須上？", expanded=False):
            st.markdown(reason)
        if not checked:
            triggered_missing.append(label)
        st.markdown("")

    completed = len(SYNDICATION_SAFEGUARDS) - len(triggered_missing)
    total = len(SYNDICATION_SAFEGUARDS)

    st.markdown("---")
    st.markdown("##### 📊 防護鎖到位度")
    p1, p2, p3 = st.columns(3)
    p1.metric("已到位", f"{completed} / {total}")
    p2.metric(
        "安全等級",
        ["🚨 裸奔", "🔴 高危", "🟠 不足", "🟡 接近", "✅ 滿載"][completed],
    )
    p3.metric(
        "可否簽合資協議",
        "✅ GO" if completed == total else "❌ 停",
        delta_color="off",
    )
    st.progress(completed / total)

    if triggered_missing:
        st.error(
            f"🚫 **資金裸奔中！** 還有 **{len(triggered_missing)} 道法律防護鎖未上**：\n\n"
            + "\n".join(f"- ❌ {item}" for item in triggered_missing)
            + "\n\n---\n\n"
            "沒有這四道防護鎖，合資買房**最後 90% 機率會翻臉上法院**——\n"
            "- 股東鬧分家 → 房子卡死\n"
            "- 登記人個人欠債 → 房子被法拍\n"
            "- 登記人偷偷過戶 → 全體股東血本無歸\n"
            "- 退場違約 → 撕破臉互告\n\n"
            "👉 **學長動作清單：**\n"
            "1. **立刻找熟悉合資的律師**起草『**合資協議書 + 信託契約**』\n"
            "2. **二順位抵押權 + 預告登記**同步辦理（一次跑完地政事務所）\n"
            "3. 退場機制白紙黑字寫死——**金額 + 期限 + 違約金**全要列\n"
            "4. **法律文件未到位前，一毛錢都不要先匯！**"
        )
    else:
        st.success(
            "✅ **四道防護鎖全數到位！**\n\n"
            "你已經做好了**合資買房最關鍵的法律準備**。\n"
            "現在可以放心進場，**讓集資的火力發揮 5 倍效益**。\n\n"
            "👉 **接下來的工作流程：**\n"
            "1. 走 Ch.4 科目四金流過水 SOP\n"
            "2. 找到目標物件後，回到上一頁推演套利金額\n"
            "3. 簽約前再請律師複核所有文件一次\n"
            "4. 簽約日**所有股東到齊**親簽，避免代簽糾紛"
        )


def render_strategy_syndication() -> None:
    """🤝 合資套利與科目四無限槓桿（進階策略）

    兩個分頁：
        1. 合資無本套利推演（破盤買進 → 半年後增貸抽本金）
        2. 合資產權絕對防護鎖（奇數股東 / 二順位 / 預告登記 / 退場機制）
    """
    st.title("🤝 合資套利與科目四無限槓桿")
    st.info(
        "💡 **學長的實戰金句**：「**有錢人不是錢比你多，是『集資』的本事比你強**。\n"
        "一個人買不起豪宅，五個人就買得起；\n"
        "一個人砸不出破盤價，五個人聯合就能讓屋主跪著賣。」"
    )

    tab_arb, tab_safe = st.tabs(
        ["💰 合資無本套利推演", "🔐 合資產權絕對防護鎖"]
    )

    with tab_arb:
        _render_arbitrage_tab()

    with tab_safe:
        _render_safeguard_tab()


# 允許 `streamlit run strategy_syndication.py` 直接預覽
if __name__ == "__main__":
    st.set_page_config(
        page_title="合資套利與科目四無限槓桿",
        page_icon="🤝",
        layout="wide",
    )
    render_strategy_syndication()
