"""Chapter 3：學長 — 出租策略與滿租定價法

獨立模組：提供 render_chapter_3() 函式，可被主程式 (main.py) import 使用。

    from chapter_3 import render_chapter_3
    render_chapter_3()
"""

import streamlit as st


# ===== 學長獨家係數對照表 =====
FLOOR_COEF_MAP: dict[str, float] = {
    "1-2 樓": 0.9,
    "3-5 樓": 1.0,
    "6 樓以上": 1.1,
}
AGE_COEF_MAP: dict[str, float] = {
    "5 年內": 1.2,
    "5-10 年": 1.0,
    "10 年以上": 0.8,
}

# 七道信用防線題目（前六道）與魔王題
GENERAL_CHECKS: list[tuple[str, str]] = [
    ("① 是否查驗交通罰單無遲繳紀錄？（測信用意識）", "ch3_tn_traffic"),
    ("② 是否已打電話至租客公司照會確認在職？", "ch3_tn_employer"),
    ("③ 司法院簡易判決書查詢是否無前科？", "ch3_tn_court"),
    ("④ 警政署 APP 查詢是否無通緝／報案紀錄？", "ch3_tn_police"),
    ("⑤ 是否能提供有力的連帶保證人？", "ch3_tn_guarantor"),
    ("⑥ 居住人數與關係是否單純交代清楚？", "ch3_tn_household"),
]
BOSS_LABEL = "⑦ 【魔王題】租客『沒有』一開口就要求押金分期 / 押金優惠？"
POINTS_PER_ITEM = 15
TOTAL_MAX_SCORE = POINTS_PER_ITEM * 7  # 105
PASS_THRESHOLD = 75
EXCELLENT_THRESHOLD = 90


def _render_pricing_tab() -> None:
    """分頁一：滿租科學定價計算機"""
    st.subheader("🎯 滿租科學定價計算機")
    st.caption("學長公式：基礎租金 × 樓層係數 × 屋齡係數 = 建議極限租金")

    col_a, col_b = st.columns(2)
    with col_a:
        avg_rent_per_ping = st.number_input(
            "區域平均單坪租金（元 / 坪）",
            min_value=0,
            value=1200,
            step=50,
            help="參考實價登錄租賃案件，取近期同區、相近屋型的中位數。",
        )
        ping_size = st.number_input(
            "房屋坪數（坪）",
            min_value=0.0,
            value=25.0,
            step=0.5,
            format="%.1f",
        )
    with col_b:
        floor_choice = st.selectbox(
            "所在樓層",
            list(FLOOR_COEF_MAP.keys()),
            index=1,
            help="低樓層治安/採光較差打 9 折；高樓層視野/採光較好加 1 成。",
        )
        age_choice = st.selectbox(
            "房屋屋齡",
            list(AGE_COEF_MAP.keys()),
            index=1,
            help="新屋附加感較強加 2 成；老屋打 8 折避免空租。",
        )

    floor_coef = FLOOR_COEF_MAP[floor_choice]
    age_coef = AGE_COEF_MAP[age_choice]

    # 核心計算
    base_rent = avg_rent_per_ping * ping_size
    suggested_rent = base_rent * floor_coef * age_coef

    st.markdown("---")
    st.markdown("##### 📊 學長定價公式拆解")
    m1, m2, m3 = st.columns(3)
    m1.metric("基礎租金", f"{base_rent:,.0f} 元", help="平均單坪租金 × 坪數")
    m2.metric("樓層係數", f"× {floor_coef}", help=floor_choice)
    m3.metric("屋齡係數", f"× {age_coef}", help=age_choice)

    st.metric(
        "🎯 建議極限租金（上架價）",
        f"{suggested_rent:,.0f} 元 / 月",
        delta=f"{(suggested_rent - base_rent):,.0f} 元 vs 基礎租金",
        help="這是市場能接受的上限。實際上架可從此數字試水溫，1~2 週無人詢問再考慮微調。",
    )
    st.caption(f"≒ 約 {suggested_rent / 10_000:.2f} 萬／月")

    # 動態降價停損監控
    st.markdown("---")
    st.markdown("##### ⏰ 空租天數監控（階梯式降價停損）")
    vacancy_days = st.slider(
        "目前已空租天數",
        min_value=0,
        max_value=90,
        value=10,
        step=1,
        help="超過 20 天就要主動下殺，不要硬撐。",
    )
    if vacancy_days > 20:
        floor_price = suggested_rent * 0.85
        step1 = suggested_rent * 0.95
        step2 = suggested_rent * 0.92
        st.warning(
            f"⚠️ **空租超過 20 天！學長建議立刻啟動階梯式降價：**\n\n"
            f"- 第一階：先降 **5%** → 約 **{step1:,.0f} 元**\n"
            f"- 第二階：若無效再降 **3%** → 約 **{step2:,.0f} 元**\n"
            f"- 🚧 **極限不可超過原價 15%** → 不可低於 **{floor_price:,.0f} 元**\n\n"
            "**再低就是賠錢做功德了。**"
        )
    elif vacancy_days > 10:
        st.info("🟡 空租已超過 10 天，再觀察一週。檢查照片、標題、看房時段是否友善。")
    else:
        st.success("🟢 空租天數在安全範圍內，維持現有策略繼續累積看屋人潮。")


def _render_radar_tab() -> None:
    """分頁二：租客七道信用防線雷達"""
    st.subheader("🛡️ 租客七道信用防線雷達")
    st.caption(
        f"七題勾選 × 每題 {POINTS_PER_ITEM} 分 = 滿分 {TOTAL_MAX_SCORE}。"
        "第 ⑦ 題為魔王題，未過直接判退。"
    )

    col_l, col_r = st.columns(2)
    general_results: list[bool] = []
    for idx, (label, key) in enumerate(GENERAL_CHECKS):
        target_col = col_l if idx < 3 else col_r
        with target_col:
            general_results.append(st.checkbox(label, key=key))

    st.markdown("---")
    boss_ok = st.checkbox(BOSS_LABEL, key="ch3_tn_boss")

    # 評分計算
    passed_count = sum(general_results) + (1 if boss_ok else 0)
    total_score = passed_count * POINTS_PER_ITEM

    st.markdown("---")
    st.markdown("##### 📊 防線評分結果")
    s1, s2, s3 = st.columns(3)
    s1.metric("通過項數", f"{passed_count} / 7")
    s2.metric("總分", f"{total_score} / {TOTAL_MAX_SCORE} 分")
    s3.metric("魔王題", "✅ 通過" if boss_ok else "❌ 失守")

    # 診斷判定
    if (not boss_ok) or total_score < PASS_THRESHOLD:
        failure_reasons: list[str] = []
        if not boss_ok:
            failure_reasons.append("**魔王題失守**：對方一開口就談押金分期 / 優惠")
        if total_score < PASS_THRESHOLD:
            failure_reasons.append(
                f"**總分不及格**：{total_score} 分 < {PASS_THRESHOLD} 分門檻"
            )
        st.error(
            "🚫 **高危險租客！**\n\n"
            + "\n".join(f"- {r}" for r in failure_reasons)
            + "\n\n連押金都付不出來或信用有瑕疵，未來極高機率變租霸——"
            "**寧可空租絕對不租！**"
        )
    elif total_score >= EXCELLENT_THRESHOLD:
        st.success(
            f"✅ **優質租客！** 總分 {total_score} / {TOTAL_MAX_SCORE}，七道防線全數過關。\n\n"
            "👉 **立刻動作清單：**\n"
            "1. **法院公證** 租約（強制執行省下一年訴訟時間）\n"
            "2. **換裝電子鎖**（搬離當天即時更換密碼／磁扣）\n"
            "3. 押金收滿 2 個月、租金一律匯款留紀錄"
        )
    else:
        st.warning(
            f"🟡 **中等租客（{total_score} 分）**：基本門檻雖過，但安全係數不夠。\n\n"
            "建議：要求加保證人 + 押金提高為 3 個月 + 租約公證後再決定是否簽約。"
        )


def render_chapter_3() -> None:
    """💰 租金精算與優質租客雷達（Chapter 3）

    兩個分頁：
        1. 滿租科學定價計算機：基礎租金 × 樓層係數 × 屋齡係數
        2. 租客七道信用防線雷達：七題 × 15 分，魔王題不可失守
    """
    st.title("💰 租金精算與優質租客雷達")
    st.info(
        "💡 **學長的實戰金句**：「寧可空租一個月，也不要租給麻煩客。"
        "租客選錯，整年白做工；房子被搞爛，五年的租金都不夠補。」"
    )

    tab_pricing, tab_radar = st.tabs(
        ["🎯 滿租科學定價計算機", "🛡️ 租客七道信用防線雷達"]
    )

    with tab_pricing:
        _render_pricing_tab()

    with tab_radar:
        _render_radar_tab()


# 允許 `streamlit run chapter_3.py` 直接預覽此單一模組
if __name__ == "__main__":
    st.set_page_config(
        page_title="Ch.3 租金精算與租客雷達",
        page_icon="💰",
        layout="wide",
    )
    render_chapter_3()
