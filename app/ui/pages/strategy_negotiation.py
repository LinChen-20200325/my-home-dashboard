"""Strategy Negotiation UI — 極限議價與談判心理戰（重構後）。

UI 層：純 widgets + 渲染；定錨單價 / 獵殺單價 / 最終出價由 services.pricing。
"""

from __future__ import annotations

import streamlit as st

from app.services.pricing import (
    final_offer_wan as compute_final_offer_wan,
    negotiation_anchor_unit_wan,
    negotiation_kill_shot_unit_wan,
)


LISTING_AGE_OPTIONS: list[str] = [
    "剛上架（< 1 個月）", "1~3 個月", "超過半年",
]
CONTRACT_TYPE_OPTIONS: list[str] = ["專任約", "一般約"]
TITLE_LIEN_OPTIONS: list[str] = [
    "🟢 乾淨（無他項權利）",
    "🟡 有銀行貸款",
    "🔴 有民間私人設定",
]


def _render_input_column() -> dict:
    st.markdown("### 🎯 談判籌碼輸入區")
    st.caption("學長心法：『籌碼蒐集得越完整，刀就磨得越利。』")

    asking_price_wan = st.number_input(
        "房仲報價 / 屋主開價（萬）",
        min_value=0.0, value=1_500.0, step=10.0, format="%.1f",
        help="目前牆上掛的『心願價』。", key="strat_neg_asking",
    )
    ad_unit_price_wan = st.number_input(
        "該建案最低『廣告戶』單價（萬／坪）",
        min_value=0.0, value=45.0, step=0.5, format="%.1f",
        help="實價登錄拉出來該社區同棟近 1 年成交『最低』那筆——這是你的定錨點。",
        key="strat_neg_ad_price",
    )
    listing_age = st.selectbox(
        "待售時間", options=LISTING_AGE_OPTIONS, index=1,
        help="越久沒賣掉，屋主越焦躁——你的籌碼越大。",
        key="strat_neg_listing_age",
    )
    contract_type = st.radio(
        "委託型態", options=CONTRACT_TYPE_OPTIONS, horizontal=True, index=1,
        help="專任約：只有一家仲介；一般約：多家仲介互搶。",
        key="strat_neg_contract_type",
    )
    title_lien = st.selectbox(
        "謄本他項權利部", options=TITLE_LIEN_OPTIONS, index=1,
        help="調閱第二類謄本一張只要 20 元——這資訊不查就出價，等於蒙眼走鋼索。",
        key="strat_neg_title_lien",
    )

    return {
        "asking_price_wan": asking_price_wan,
        "ad_unit_price_wan": ad_unit_price_wan,
        "listing_age": listing_age,
        "contract_type": contract_type,
        "title_lien": title_lien,
    }


def _render_strategy_column(payload: dict) -> None:
    st.markdown("### 🎲 戰術生成與底價推演")
    st.caption("學長心法：『買房不是議價，是『**獵屋**』——獵人不會跟獵物講價。』")

    asking = payload["asking_price_wan"]
    ad_unit = payload["ad_unit_price_wan"]
    listing_age = payload["listing_age"]
    contract_type = payload["contract_type"]
    title_lien = payload["title_lien"]

    # ---------- 底價推演引擎 ----------
    st.markdown("##### 🎯 底價推演引擎")

    if title_lien.startswith("🔴"):
        kill_unit = negotiation_kill_shot_unit_wan(ad_unit)
        st.success(
            "🎯 **獵物確認！** 他項權利部出現『**私人姓名**』——\n\n"
            "白話翻譯：屋主向地下錢莊借錢，**現金週轉極度吃緊**。\n"
            "他每天醒來想的不是『要賣多少』，而是『**今天能不能撐過**』。\n\n"
            "👉 **學長戰術：直接用實價登錄最低均價『再往下砍 10%』作為初次出價！**\n\n"
            f"以這案為例：廣告戶單價 **{ad_unit:.1f} 萬／坪**——"
            f"你的首槍應該定錨在 **{kill_unit:.1f} 萬／坪**，"
            "然後**鐵著臉**告訴仲介『現金、不貸款、3 天可付訂』。\n\n"
            "**這種獵物你不下手，明天就被別的獵人扛走。**"
        )
    elif title_lien.startswith("🟢"):
        st.info(
            "🟢 **謄本乾淨**——屋主沒有金錢急迫性，"
            "議價空間大概只能砍 **5-10%**。但別灰心，下面的戰術一樣管用。"
        )
    else:
        st.warning(
            "🟡 **有銀行貸款設定**——你要做的功課是：\n"
            "**逆推屋主剩餘本金**（買入年份 + 推估貸款餘額）。\n"
            "他的『**剩餘本金 + 5%**』就是他的真正心理底線。"
        )

    if contract_type == "一般約":
        st.info(
            "💡 **一般約 → 房仲業績壓力極大！**\n\n"
            "因為同一間房可能有 3-5 家仲介在搶，誰先成交誰拿佣金。\n\n"
            "👉 **學長戰術：暗示房仲『別家也在推這間，但價錢比你便宜』**——\n"
            "他會立刻打電話給屋主『**強壓**』報價，因為他怕你被別家搶走。"
        )
    else:
        st.warning(
            "🟠 **專任約 → 房仲壟斷這筆生意**，沒有業績壓力比較。\n\n"
            "**話術改成**：『我看了 3 間類似條件，這間貴 X 萬。"
            "你能幫我跟屋主溝通嗎？不然我先去看別的。』"
        )

    if listing_age == "超過半年":
        st.success(
            "⏰ **賣超過半年——屋主已經疲勞轟炸**。\n"
            "這時候你出『**他不舒服但忍痛能接**』的價，他大概率會點頭。"
        )
    elif listing_age == "1~3 個月":
        st.caption("⏳ 上架 1-3 個月——屋主開始焦慮，可砍 **8-12%**。")
    else:
        st.caption("🆕 剛上架——屋主心氣正高，可能要等 1-2 個月再回頭談。")

    st.markdown("---")

    # ---------- 包廂議價三戰術 ----------
    st.markdown("##### 🎭 包廂議價三戰術（按順序執行）")
    anchor_unit = negotiation_anchor_unit_wan(ad_unit)

    with st.container():
        st.markdown("**🎯 戰術 1：定錨效應**")
        st.markdown(
            f"請**直接拿『廣告戶的單價 {ad_unit:.1f} 萬／坪』作為你的談判天花板**，"
            "**從單價開始談，絕對不要一開口就談總價！**\n\n"
            "👉 **話術範本：**\n"
            f"> 「我看了實價登錄，這社區最低成交是 **{ad_unit:.1f} 萬／坪**。\n"
            f"> 我願意付 **{anchor_unit:.1f} 萬／坪** 一次到位，"
            "請你幫我跟屋主談。」\n\n"
            "**對方一旦進入『單價框架』，就跳不出來——這就是定錨效應的威力。**"
        )

    st.markdown("---")

    with st.container():
        st.markdown("**👥 戰術 2：黑白臉戰術**")
        st.markdown(
            "**看屋時務必啟動雙簧！**\n\n"
            "- **帶長輩（爸 / 媽 / 大哥）扮黑臉**：\n"
            "  「這房子西曬欸」「廚房好舊」「樓下小吃店油煙好重」"
            "「你看那個天花板有水痕」\n\n"
            "- **你扮白臉**：\n"
            "  「可是這個地段真的不錯」「裝潢可以慢慢改」"
            "「但是預算真的有限⋯」\n\n"
            "**心理學原理**：屋主／仲介看到一個人嫌、一個人想買，"
            "會把希望寄託在『白臉』身上——**主動降價來促成交**，"
            "因為他覺得『黑臉』隨時可能否決這筆。\n\n"
            "👉 **進階技巧：黑臉一定要演到底**——\n"
            "走出去那一刻還要在電梯裡放話：『**這價錢回家再說**』。"
        )

    st.markdown("---")

    final_offer = compute_final_offer_wan(asking)
    with st.container():
        st.markdown("**🛡️ 戰術 3：收尾擋箭牌**")
        st.markdown(
            "當價格卡住時、雙方僵持在 5-10 萬內，**丟出最後底牌**：\n\n"
            "👉 **話術範本（擇一使用，每次只用一個）：**\n\n"
            "**A. 整修擋箭牌**：\n"
            "> 「我請室內設計師估過了，**水電要重拉、廚衛要翻新、防水要重做**，"
            "至少 **100 萬**。\n"
            "> 你再讓 **50 萬**幫我吸收一半工程款，我今天就下訂。」\n\n"
            "**B. 資金擋箭牌**：\n"
            "> 「我家人原本承諾的資金**卡在股票被套**，\n"
            "> 你能不能再讓 **50 萬零頭**？我加上自備款剛好能買。」\n\n"
            "**C. 比較擋箭牌**：\n"
            "> 「我看的另一間社區，**單價低你這 1.5 萬**，但通勤多 5 分鐘。\n"
            "> 你讓 **50 萬**，我選你這間。」\n\n"
            f"📊 **以這案：建議最終出價 ≈ {final_offer:,.1f} 萬**"
            f"（開價 {asking:,.0f} × 85% − 50 萬零頭）"
        )

    st.markdown("---")
    st.error(
        "⚠️ **學長最後叮嚀**：**砍價是談判，不是吵架**。\n\n"
        "全程語氣保持平穩，**讓對方覺得你『不是非買不可』**——"
        "這才是議價的最高境界。\n\n"
        "**你越想要，價錢就越貴；你越無所謂，價錢自己會掉下來。**"
    )


def render_strategy_negotiation() -> None:
    """💼 極限議價與談判心理戰（進階策略）— UI 入口。"""
    st.title("💼 極限議價與談判心理戰")
    st.info(
        "💡 **學長的實戰金句**：「**買房不是議價，是『獵屋』**。\n"
        "獵人不會跟獵物講價——獵人只會挑時機、選工具，**一槍致命**。」"
    )

    col_left, col_right = st.columns([1, 1.3], gap="large")
    with col_left:
        payload = _render_input_column()
    with col_right:
        _render_strategy_column(payload)
