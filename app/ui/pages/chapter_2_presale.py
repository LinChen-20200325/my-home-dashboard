"""Chapter 2 UI — 預售屋『買就賺』選址與合約快篩（重構後）。

UI 層：純 widgets + 渲染；公式 / 判定全部委派給 services.presale_filter。
"""

from __future__ import annotations

import streamlit as st

from app.models.constants import ELEVATOR_RATIO_DANGER
from app.models.property import PropertySpec, PropertyType
from app.services.presale_filter import (
    ElevatorRatioGrade,
    EscrowSeverity,
    EscrowType,
    classify_escrow,
    diagnose_contract_landmines,
    grade_elevator_ratio,
)


# ===== UI 標籤 → 內部 enum 對照 =====
ESCROW_LABEL_BY_TYPE: dict[EscrowType, str] = {
    EscrowType.PRICE_RETURN: "✅ 價金返還保證（最強，建商倒了銀行原額退款）",
    EscrowType.PRICE_TRUST: "🟡 價金信託（中等，銀行控管但仍有撥款風險）",
    EscrowType.PEER_CO_GUARANTEE: "🟠 同業連帶擔保（次差,建商互保但有連動風險）",
    EscrowType.DEVELOPMENT_TRUST: "🔴 不動產開發信託(最弱,只管帳不管退款)",
}
_LABEL_TO_ESCROW: dict[str, EscrowType] = {v: k for k, v in ESCROW_LABEL_BY_TYPE.items()}

BUILDER_HEALTH_CHECKS: list[tuple[str, str]] = [
    ("① 建商資本額**大於 2 億元**（夠厚才不會中途斷頭）", "ch2_builder_capital"),
    ("② 成立**超過 5-10 年**，且有 **1-2 個以上完工建案**", "ch2_builder_history"),
    ("③ 履約保證提供『**價金返還保證**』（出事可拿回現金）", "ch2_builder_guarantee"),
]

CONTRACT_LANDMINES: list[tuple[str, str, str]] = [
    (
        "① 合約偷將『雨遮／屋簷』計入價格",
        "ch2_contract_eaves",
        "📜 **法源**：民國 105 年起新建案雨遮**不登記面積、不計價**（內政部 105.1.1 函）。"
        "你看到的合約還在偷塞雨遮計價，**就是欺負你不懂法律**。",
    ),
    (
        "② 交屋後實際面積與合約**誤差 > 3%**",
        "ch2_contract_area_error",
        "📜 **法源**：預售屋定型化契約應記載事項第 7 條——"
        "「面積誤差超過 3% 者，買方得解除契約」。\n\n"
        "**白話翻譯：超過 3% 你可以直接退屋拿回全款，建商不能阻止。**",
    ),
    (
        "③ 貸款核貸不足 **30%** 時，合約**沒有**保障買方可解約",
        "ch2_contract_loan_clause",
        "📜 **法源**：預售屋定型化契約應記載事項第 18 條——"
        "「貸款金額不足原預定貸款金額 30% 以上時，買方得解除契約」。\n\n"
        "**如果你的合約沒有寫清楚，就是建商藏陷阱——簽下去等於放棄這條救命條款。**",
    ),
]


def _render_builder_health() -> None:
    st.markdown("### 🏗️ 區塊一：建商體質體檢")
    st.caption("學長心法：『建商選錯，再好的地段也會變成爛尾樓。』")

    builder_results = [st.checkbox(label, key=key) for label, key in BUILDER_HEALTH_CHECKS]

    st.markdown("---")
    st.markdown("##### 🛡️ 履約保證類型（請選擇你看到的合約寫法）")
    label_options = list(ESCROW_LABEL_BY_TYPE.values())
    guarantee_choice = st.radio(
        "履約保證條款",
        options=label_options,
        index=0,
        key="ch2_guarantee_type",
        label_visibility="collapsed",
    )
    escrow_severity = classify_escrow(_LABEL_TO_ESCROW[guarantee_choice])

    passed = sum(builder_results)
    total = len(BUILDER_HEALTH_CHECKS)

    if escrow_severity in (EscrowSeverity.MODERATE, EscrowSeverity.HIGH_RISK):
        st.warning(
            "⚠️ **履保警報！** 你選的不是『價金返還保證』——\n\n"
            "- **價金信託**：銀行控管金流，但建商出事時，工程款已撥付的部分**拿不回來**（有殘值風險）\n"
            "- **同業連帶擔保**：互保建商若同時景氣不好，可能**一倒全倒**\n\n"
            "👉 **學長建議**：要求建商修改為『價金返還保證』，否則風險太高，"
            "**寧可不買也不要簽**。"
        )
    elif escrow_severity == EscrowSeverity.CRITICAL:
        st.error(
            "🚫 **不動產開發信託是最弱的履保！** 建商倒了等於 0 賠償，"
            "**這種案子直接放棄，連訂金都不要付**。"
        )
    else:
        st.success("✅ 履保等級最強——『價金返還保證』，這條件 OK。")

    if passed < total:
        st.warning(
            f"🟡 建商三大體質檢核僅通過 **{passed} / {total}** 項，"
            "建議到法務部商業司查資本額、上『內政部不動產資訊平台』查過往建案。"
        )
    else:
        st.success(f"✅ 建商三大體質**全數過關**（{passed}/{total}）！")


def _render_layout_filter() -> None:
    st.markdown("### 📐 區塊二：圖面與公設快篩")
    st.caption("學長心法：『一支電梯八戶人家，上班尖峰排隊比扶輪社還久。』")

    col_a, col_b = st.columns(2)
    with col_a:
        units_per_floor = st.number_input(
            "單層戶數（戶）", min_value=1, max_value=30, value=4, step=1,
            help="這一層樓總共幾戶。", key="ch2_units_per_floor",
        )
    with col_b:
        elevator_count = st.number_input(
            "電梯數量（含貨梯）", min_value=1, max_value=10, value=2, step=1,
            help="實際運作的電梯數。", key="ch2_elevator_count",
        )

    spec = PropertySpec(PropertyType.PRESALE, 25.0, int(units_per_floor), int(elevator_count))
    ratio = spec.elevator_ratio
    grade = grade_elevator_ratio(spec)

    st.markdown("---")
    m1, m2, m3 = st.columns(3)
    m1.metric("單層戶數", f"{units_per_floor} 戶")
    m2.metric("電梯數量", f"{elevator_count} 部")
    m3.metric(
        "📊 梯戶比", f"{ratio:.2f}",
        delta=f"紅線：{ELEVATOR_RATIO_DANGER}", delta_color="inverse",
        help="戶數 ÷ 電梯數，越低越好。",
    )

    if grade == ElevatorRatioGrade.DANGEROUS:
        st.error(
            f"🚫 **梯戶比 {ratio:.2f} 過高！**\n\n"
            "未來租客上下班尖峰**等電梯會等到崩潰**，這會嚴重影響：\n"
            "- 租金天花板**直接被砍 5-15%**\n"
            "- 屋主換約週期變短（住戶忍受度低）\n"
            "- 二手轉手時，買方一聽到『8 戶 2 梯』就掉頭走\n\n"
            "👉 **學長建議**：梯戶比 ≤ 3 是安全水位，**這案請放棄**。"
        )
    elif grade == ElevatorRatioGrade.BORDERLINE:
        st.warning(
            f"🟡 梯戶比 {ratio:.2f} 偏高但勉強可接受，"
            "**租金請以區域均價下限定價**，不要硬拗高租金。"
        )
    else:
        st.success(f"✅ 梯戶比 {ratio:.2f}，動線品質優良，可衝高租金。")

    st.markdown("---")
    has_infinity_pool = st.checkbox(
        "🏊 建案有『無邊際溫水游泳池』或類似高昂公設（健身房、宴會廳、影音室等）",
        key="ch2_infinity_pool",
    )
    if has_infinity_pool:
        st.warning(
            "⚠️ **高昂公設陷阱！**\n\n"
            "無邊際溫水游泳池、五星級健身房這類公設——"
            "**買的時候算虛坪，住的時候是錢坑**：\n"
            "- 管理費 / 坪可能高達 **80-150 元**（一般 50-70 元）\n"
            "- 維護需專業團隊，**修一次幾十萬起跳**\n"
            "- 你的租客大概率用不到，但**每月都要分攤**\n\n"
            "👉 **學長建議**：評估你的目標租客是否願意承擔——"
            "如果是要租給小資族或學生，**管理費太貴會直接打掉租金競爭力**。"
        )


def _render_contract_landmines() -> None:
    st.markdown("### ⚠️ 區塊三：定型化契約地雷掃描")
    st.caption("學長心法：『建商不會主動告訴你的條款，就是專門用來坑你的條款。』")

    hits = tuple(st.checkbox(label, key=key) for label, key, _ in CONTRACT_LANDMINES)
    verdict = diagnose_contract_landmines(hits)

    if verdict.has_any_landmine:
        triggered_texts = [CONTRACT_LANDMINES[i][2] for i in verdict.triggered_indices]
        st.error(
            f"🚫 **抓到 {verdict.landmine_count} 條合約地雷！** 內政部已明文規範，"
            "建商**不能用合約凌駕法律**：\n\n"
            + "\n\n---\n\n".join(triggered_texts)
            + "\n\n---\n\n👉 **學長動作清單：**\n"
            "1. **書面要求建商修改條款**（口頭承諾無效）\n"
            "2. 不改就打 **1950 消保官** 或 **內政部地政司** 檢舉\n"
            "3. 已付訂金者，**依法定行使解約權拿回全款**\n"
            "4. **不要怕得罪建商**——你不買，下一個冤大頭很快會出現"
        )
    else:
        st.success(
            "✅ 三大合約地雷皆未踩到。但學長提醒：**簽約前還是要請代書或律師複核全文**，"
            "魔鬼藏在小字裡。"
        )


def render_chapter_2() -> None:
    """🏗️ 預售屋：買就賺選址與合約快篩（Chapter 2）— UI 入口。"""
    st.title("🏗️ 預售屋：買就賺選址與合約快篩")
    st.info(
        "💡 **學長的實戰金句**：「**預售屋的利潤鎖在『簽約那一刻』，不是交屋那一刻。**\n"
        "便宜不是省下來的，是『選』下來的——選錯地段、選錯建商，"
        "再大的折扣都是糖衣。」"
    )

    _render_builder_health()
    st.markdown("---")
    _render_layout_filter()
    st.markdown("---")
    _render_contract_landmines()
