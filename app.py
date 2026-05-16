"""
Ziv學長：買房前自我能力與現金流健檢（整合完整版）
整合三份 Excel 公式：
  1. 05768 完整版：PMT 房貸引擎、寬限期、現金流、投資回收、房價增值3情境、利率/空租風險
  2. 1e812 懶人包：租金安全指數、底線租金
  3. 5f74150 個人負債比與房貸能力試算 + 反推所需月收入
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ===================== 頁面基礎設定 =====================
st.set_page_config(
    page_title="Ziv學長：買房前自我能力與現金流健檢",
    page_icon="🏠",
    layout="wide",
)


# ===================== 公式工具函式 =====================
def pmt(monthly_rate: float, n_periods: int, principal: float) -> float:
    """本息平均攤還月付金（對應 Excel PMT）"""
    if n_periods <= 0 or principal <= 0:
        return 0.0
    if monthly_rate <= 0:
        return principal / n_periods
    factor = (1 + monthly_rate) ** n_periods
    return principal * monthly_rate * factor / (factor - 1)


def amortization_schedule(principal, annual_rate, years, grace_years=0):
    """逐月攤還表：月付金、利息、本金、剩餘本金"""
    monthly_rate = annual_rate / 12
    total_m = int(years * 12)
    grace_m = int(min(grace_years, years) * 12)
    pay_m = total_m - grace_m

    grace_pay = principal * monthly_rate
    post_pay = pmt(monthly_rate, pay_m, principal) if pay_m > 0 else 0.0

    rows = []
    balance = principal
    for m in range(1, total_m + 1):
        if m <= grace_m:
            payment = grace_pay
            interest = principal * monthly_rate
            principal_paid = 0.0
        else:
            payment = post_pay
            interest = balance * monthly_rate
            principal_paid = payment - interest
            balance = max(balance - principal_paid, 0.0)
        rows.append(
            {
                "期數": m,
                "年度": (m - 1) // 12 + 1,
                "月付金": payment,
                "利息": interest,
                "本金": principal_paid,
                "剩餘本金": balance,
            }
        )
    return pd.DataFrame(rows)


# ===================== 標題區 =====================
st.title("🏠 Ziv學長：買房前自我能力與現金流健檢")
st.caption(
    "整合 Ziv學長三份實戰試算表：階級現金流診斷 × 貸款資格 × PMT 房貸引擎 × "
    "投資收益 × 風險壓力測試 × 租金安全懶人包。所有數字會跟著側邊欄即時連動。"
)


# ===================== 側邊欄輸入區 =====================
with st.sidebar:
    st.header("📋 現況輸入區")
    st.caption("先把所有參數設定好，分頁圖表會自動同步。")

    with st.expander("👤 個人基本條件", expanded=True):
        age = st.number_input("目前年齡", 18, 80, 30, 1)
        loan_years = st.number_input("預計申請貸款年限（年）", 10, 40, 30, 5)

    with st.expander("💵 收支金流", expanded=True):
        monthly_income = st.number_input("每月總收入", 0, value=60_000, step=1_000)
        annual_bonus = st.number_input("每年獎金（年終、季獎）", 0, value=120_000, step=10_000)
        other_income = st.number_input("每月其他收入（兼職/投資）", 0, value=0, step=1_000)
        monthly_bad_debt = st.number_input(
            "每月壞債支出（信貸/車貸/卡循）", 0, value=10_000, step=1_000,
        )
        monthly_living = st.number_input("每月生活開銷（含保險娛樂）", 0, value=25_000, step=1_000)

    with st.expander("🏦 財力證明", expanded=False):
        total_assets = st.number_input("名下總資產估值", 0, value=2_000_000, step=10_000)
        total_liabilities = st.number_input("名下總負債餘額", 0, value=500_000, step=10_000)
        cash_reserve = st.number_input("現金存款（緊急預備金來源）", 0, value=500_000, step=10_000)

    with st.expander("🏠 房屋與貸款條件", expanded=True):
        house_price = st.number_input("房屋總價", 0, value=10_000_000, step=100_000)
        down_payment = st.number_input("自備款", 0, value=2_000_000, step=100_000)
        renovation = st.number_input("裝潢費用", 0, value=300_000, step=10_000)
        other_fees = st.number_input("其他費用（代書/稅費）", 0, value=50_000, step=10_000)
        annual_rate_pct = st.number_input(
            "貸款年利率（%）", 0.0, 10.0, 2.5, 0.05, format="%.2f"
        )
        grace_years = st.number_input("寬限期（年，只繳利息）", 0, 10, 5, 1)

    with st.expander("📈 租金與投資", expanded=False):
        rent = st.number_input("預估月租金", 0, value=35_000, step=1_000)
        mgmt_fee = st.number_input("月管理費＋稅", 0, value=2_000, step=500)
        vacancy_discount = st.slider(
            "空置保守打折比例（懶人包公式）", 0.0, 0.5, 0.10, 0.01,
            help="0.10 代表打 9 折；越保守可拉到 0.20",
        )
        repair_pct = st.slider(
            "維修小金庫（佔租金 %）", 0.0, 0.2, 0.05, 0.01,
            help="新屋預設 5%、老屋建議 10%",
        )

    with st.expander("⚠️ 風險壓力測試參數", expanded=False):
        location_rating = st.select_slider(
            "房屋地段等級",
            options=[1, 2, 3, 4, 5],
            value=2,
            format_func=lambda x: {1: "1 精華", 2: "2 優良", 3: "3 一般", 4: "4 偏遠", 5: "5 極偏"}[x],
        )
        vacancy_months = st.number_input("年度空租月數預估", 0, 12, 2, 1)


# ===================== 核心計算 =====================
annual_rate = annual_rate_pct / 100
total_monthly_income = monthly_income + annual_bonus / 12 + other_income
total_monthly_expense = monthly_living + monthly_bad_debt
monthly_surplus = total_monthly_income - total_monthly_expense
bad_debt_ratio = monthly_bad_debt / total_monthly_income if total_monthly_income > 0 else 0.0
age_plus_loan = age + loan_years
asset_liability_ratio = (
    total_assets / total_liabilities if total_liabilities > 0 else float("inf")
)

# 房貸計算引擎
loan_amount = max(house_price - down_payment, 0)
ltv = loan_amount / house_price if house_price > 0 else 0
total_investment = down_payment + renovation + other_fees
monthly_rate = annual_rate / 12
total_months = int(loan_years * 12)
grace_months = int(min(grace_years, loan_years) * 12)
pay_months = total_months - grace_months

grace_payment = loan_amount * monthly_rate
post_grace_payment = pmt(monthly_rate, pay_months, loan_amount) if pay_months > 0 else 0
avg_monthly_payment = (
    (grace_payment * grace_months + post_grace_payment * pay_months) / total_months
    if total_months > 0 else 0
)
total_interest = (
    grace_payment * grace_months + post_grace_payment * pay_months - loan_amount
)
total_repayment = total_interest + loan_amount
interest_ratio = total_interest / total_repayment if total_repayment > 0 else 0

# 含房貸的 DTI（送件用）
mortgage_dti = (
    (monthly_bad_debt + post_grace_payment) / total_monthly_income
    if total_monthly_income > 0 else 1.0
)


# ===================== 分頁區 =====================
tab_check, tab_loan, tab_cash, tab_invest, tab_risk, tab_lazy = st.tabs(
    [
        "🩺 體質檢測",
        "💰 房貸試算引擎",
        "📈 現金流還款分析",
        "🏠 投資收益情境",
        "⚠️ 風險壓力測試",
        "📋 租金安全懶人包",
    ]
)


# ======================================================
# Tab 1：體質檢測（原區塊一+區塊二）
# ======================================================
with tab_check:
    st.header("一、階級現金流與財富思維診斷")
    st.caption("PPT 第一課：『不是收入決定階級，而是現金流決定階級。』")

    c1, c2, c3 = st.columns(3)
    c1.metric("每月總收入（含獎金均攤）", f"NT$ {total_monthly_income:,.0f}")
    c2.metric(
        "每月結餘",
        f"NT$ {monthly_surplus:,.0f}",
        delta=f"{monthly_surplus:,.0f}",
        delta_color="normal" if monthly_surplus >= 0 else "inverse",
    )
    c3.metric("壞債佔收入比", f"{bad_debt_ratio * 100:.1f}%")

    if monthly_surplus < 0:
        st.error(
            "⚠️ **窮人現金流：努力工作賺錢，然後把錢花光。**\n\n"
            "你目前的現金流是 **負的**，先專注節流並清除信用卡、卡循等壞債，"
            "把現金流拉回正號，才有資格進入下一階段。"
        )
    elif monthly_surplus > 0 and bad_debt_ratio > 0.15:
        st.warning(
            "⚠️ **中產階級迷思：把花錢的東西當成資產。**\n\n"
            f"結餘雖正（+NT$ {monthly_surplus:,.0f}），但壞債佔比 "
            f"{bad_debt_ratio * 100:.1f}%（>15%）。請先還清車貸／信貸／卡循，"
            "區分『好債（買生錢資產）』與『壞債（買花錢負債）』，才能開啟低利房貸槓桿。"
        )
    else:
        st.success(
            "✅ **富人現金流！恭喜你具備累積『好債』的能力。**\n\n"
            f"每月結餘 +NT$ {monthly_surplus:,.0f}，壞債比僅 {bad_debt_ratio * 100:.1f}%。"
            "下一步：建立信用、養財力證明，向銀行借低息房貸買進生錢資產。"
        )

    st.divider()
    st.header("二、房產貸款資格實戰檢核")
    st.caption("PPT 第二課：『銀行不是看你多有錢，是看你能不能還、值不值得借。』")

    ca, cb, cc = st.columns(3)
    ca.metric("年齡 + 貸款年限", f"{age_plus_loan} 年")
    cb.metric("壞債負債比（DTI）", f"{bad_debt_ratio * 100:.1f}%")
    cc.metric(
        "總資產 / 總負債",
        "∞ (無負債)" if total_liabilities == 0 else f"{asset_liability_ratio:.2f} 倍",
    )

    st.markdown("##### 🎯 檢核 1：年齡＋貸款年限 ≤ 75")
    if age_plus_loan > 75:
        st.error(
            f"⚠️ 年齡＋年限 = {age_plus_loan} 年，已超過 75 上限。"
            "銀行會自動縮短年限、月付金爆增。"
        )
    else:
        st.success(f"✅ 年齡＋年限 = {age_plus_loan} 年（≤ 75），通過第一道門檻。")

    st.markdown("##### 🎯 檢核 2：壞債負債比 < 70%")
    if bad_debt_ratio >= 0.70:
        st.error(f"⚠️ DTI = {bad_debt_ratio * 100:.1f}%，突破 70% 紅線，極可能被拒貸。")
    else:
        st.success(f"✅ DTI = {bad_debt_ratio * 100:.1f}%，安全通過。")

    st.markdown("##### 🎯 檢核 3：總資產負債比 > 1.5")
    if total_liabilities == 0:
        st.success("🚀 **無敵財力證明：你目前無任何負債！** 銀行幾乎搶著放款。")
    elif asset_liability_ratio > 1.5:
        st.success(
            f"🚀 **無敵財力證明：資產負債比 = {asset_liability_ratio:.2f} 倍！** "
            "可爭取最高成數＋最低利率。"
        )
    else:
        st.warning(
            f"⚠️ 資產負債比 = {asset_liability_ratio:.2f} 倍（≤ 1.5），財力證明偏弱。"
            "建議集中定存單、整理對帳單，6~12 個月後再送件。"
        )


# ======================================================
# Tab 2：房貸試算引擎（PMT + 寬限期 + 攤還曲線）
# ======================================================
with tab_loan:
    st.header("💰 房貸試算引擎（PMT + 寬限期）")
    st.caption("公式來源：Excel 房貸計算引擎 — PMT 本息攤還、寬限期只繳利息、利率敏感度。")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("貸款金額", f"NT$ {loan_amount:,.0f}")
    m2.metric("貸款成數 (LTV)", f"{ltv * 100:.1f}%")
    m3.metric("總投資成本", f"NT$ {total_investment:,.0f}", help="自備款＋裝潢＋其他費用")
    m4.metric("月利率", f"{monthly_rate * 100:.4f}%")

    st.markdown("##### 💳 月付金結構")
    p1, p2, p3 = st.columns(3)
    p1.metric("寬限期月付金", f"NT$ {grace_payment:,.0f}", help="僅繳利息")
    p2.metric("寬限期後月付金", f"NT$ {post_grace_payment:,.0f}", help="本息平均攤還")
    p3.metric("加權平均月付", f"NT$ {avg_monthly_payment:,.0f}")

    s1, s2, s3 = st.columns(3)
    s1.metric("總利息支出", f"NT$ {total_interest:,.0f}")
    s2.metric("總還款金額", f"NT$ {total_repayment:,.0f}")
    s3.metric("利息佔總還款", f"{interest_ratio * 100:.1f}%")

    st.markdown("---")
    st.markdown("##### 📉 攤還曲線（剩餘本金 + 每年本金/利息比例）")

    if loan_amount > 0 and total_months > 0:
        sched = amortization_schedule(loan_amount, annual_rate, loan_years, grace_years)
        annual = sched.groupby("年度").agg(
            年利息=("利息", "sum"),
            年本金=("本金", "sum"),
            年底剩餘=("剩餘本金", "last"),
        ).reset_index()

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(
            go.Bar(
                x=annual["年度"], y=annual["年利息"],
                name="年繳利息", marker_color="#E74C3C",
            ),
            secondary_y=False,
        )
        fig.add_trace(
            go.Bar(
                x=annual["年度"], y=annual["年本金"],
                name="年繳本金", marker_color="#27AE60",
            ),
            secondary_y=False,
        )
        fig.add_trace(
            go.Scatter(
                x=annual["年度"], y=annual["年底剩餘"],
                name="年底剩餘本金", mode="lines+markers",
                line=dict(color="#2C3E50", width=3),
            ),
            secondary_y=True,
        )
        fig.update_layout(
            barmode="stack",
            xaxis_title="貸款年度",
            yaxis_title="當年現金流出（元）",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=450,
            margin=dict(t=20, b=40),
        )
        fig.update_yaxes(title_text="當年現金流出（元）", secondary_y=False)
        fig.update_yaxes(title_text="剩餘本金（元）", secondary_y=True)
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("📑 完整逐月攤還表（前 24 期預覽）"):
            st.dataframe(
                sched.head(24).style.format(
                    {
                        "月付金": "{:,.0f}",
                        "利息": "{:,.0f}",
                        "本金": "{:,.0f}",
                        "剩餘本金": "{:,.0f}",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )
    else:
        st.info("請於側邊欄輸入房屋總價與自備款。")

    st.markdown("---")
    st.markdown("##### 📊 利率敏感度分析")
    if loan_amount > 0 and pay_months > 0:
        deltas = [-0.005, 0.0, 0.005, 0.01, 0.015, 0.02]
        rows = []
        base_pay = post_grace_payment
        for d in deltas:
            new_rate = annual_rate + d
            new_monthly_rate = new_rate / 12
            new_pay = pmt(new_monthly_rate, pay_months, loan_amount)
            rows.append(
                {
                    "利率情境": f"{new_rate * 100:.2f}%（{('+' if d >= 0 else '')}{d * 100:.1f}%）",
                    "新月付金": new_pay,
                    "月付增加": new_pay - base_pay,
                    "佔月收入比": new_pay / total_monthly_income if total_monthly_income > 0 else 0,
                }
            )
        df_rate = pd.DataFrame(rows)

        fig2 = go.Figure()
        fig2.add_trace(
            go.Bar(
                x=df_rate["利率情境"],
                y=df_rate["新月付金"],
                marker_color=["#3498DB" if d <= 0 else "#E67E22" if d <= 0.01 else "#C0392B" for d in deltas],
                text=[f"NT$ {v:,.0f}" for v in df_rate["新月付金"]],
                textposition="outside",
                name="月付金",
            )
        )
        fig2.update_layout(
            xaxis_title="利率情境",
            yaxis_title="月付金（元）",
            height=400,
            margin=dict(t=20, b=40),
        )
        st.plotly_chart(fig2, use_container_width=True)
        st.dataframe(
            df_rate.style.format(
                {"新月付金": "{:,.0f}", "月付增加": "{:,.0f}", "佔月收入比": "{:.1%}"}
            ),
            use_container_width=True,
            hide_index=True,
        )


# ======================================================
# Tab 3：現金流還款分析
# ======================================================
with tab_cash:
    st.header("📈 現金流還款分析")
    st.caption("公式來源：Excel 現金流分析（無寬限期）— 月/年現金流、累積現金流、負擔率。")

    # 兩種情境：寬限期內（只繳利息）vs 寬限期後（本息攤還）
    cf_grace = total_monthly_income - grace_payment - monthly_living - monthly_bad_debt
    cf_post = total_monthly_income - post_grace_payment - monthly_living - monthly_bad_debt
    cf_avg = total_monthly_income - avg_monthly_payment - monthly_living - monthly_bad_debt

    burden_grace = grace_payment / total_monthly_income if total_monthly_income > 0 else 0
    burden_post = post_grace_payment / total_monthly_income if total_monthly_income > 0 else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("寬限期月現金流", f"NT$ {cf_grace:,.0f}",
              delta_color="normal" if cf_grace >= 0 else "inverse")
    c2.metric("寬限後月現金流", f"NT$ {cf_post:,.0f}",
              delta_color="normal" if cf_post >= 0 else "inverse")
    c3.metric("加權平均月現金流", f"NT$ {cf_avg:,.0f}",
              delta_color="normal" if cf_avg >= 0 else "inverse")

    b1, b2, b3 = st.columns(3)
    b1.metric("純房貸負擔率（寬限後）", f"{burden_post * 100:.1f}%",
              help="銀行眼中真正的還款壓力")
    b2.metric("總貸款負擔率（含個人壞債）", f"{mortgage_dti * 100:.1f}%",
              help="若 ≥70% 銀行直接退件")
    b3.metric("送件 DTI 燈號",
              "✅ 安全" if mortgage_dti < 0.5 else ("⚠️ 注意" if mortgage_dti < 0.7 else "❌ 危險"))

    st.markdown("##### 📊 月現金流結構（含房貸 vs 不含房貸）")
    cf_breakdown = pd.DataFrame(
        {
            "項目": ["月收入", "月生活費", "月壞債", "月房貸（寬限期）", "月房貸（寬限後）"],
            "金額": [
                total_monthly_income,
                -monthly_living,
                -monthly_bad_debt,
                -grace_payment,
                -post_grace_payment,
            ],
            "類別": ["收入", "支出", "支出", "寬限期支出", "寬限後支出"],
        }
    )
    fig3 = go.Figure(
        go.Bar(
            x=cf_breakdown["項目"],
            y=cf_breakdown["金額"],
            marker_color=["#27AE60", "#E67E22", "#E67E22", "#3498DB", "#C0392B"],
            text=[f"NT$ {v:,.0f}" for v in cf_breakdown["金額"]],
            textposition="outside",
        )
    )
    fig3.update_layout(
        yaxis_title="金額（元）",
        height=380,
        margin=dict(t=20, b=40),
    )
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("##### 📈 累積現金流（30 年期）")
    years_range = list(range(1, int(loan_years) + 1))
    cumulative = []
    accum = 0.0
    for y in years_range:
        if y <= grace_years:
            yearly_cf = cf_grace * 12
        else:
            yearly_cf = cf_post * 12
        accum += yearly_cf
        cumulative.append(accum)

    fig4 = go.Figure()
    fig4.add_trace(
        go.Scatter(
            x=years_range,
            y=cumulative,
            mode="lines+markers",
            fill="tozeroy",
            line=dict(color="#16A085", width=3),
            name="累積現金流",
        )
    )
    fig4.add_hline(y=0, line_dash="dash", line_color="red")
    fig4.update_layout(
        xaxis_title="貸款年度",
        yaxis_title="累積淨現金流（元）",
        height=400,
        margin=dict(t=20, b=40),
    )
    st.plotly_chart(fig4, use_container_width=True)

    # 個人負債比 + 反推所需月收入（5f74150 邏輯）
    st.markdown("---")
    st.markdown("##### 🧮 反推所需月收入（Ziv學長 70% 紅線回推）")
    total_monthly_debt = monthly_bad_debt + post_grace_payment
    required_income = total_monthly_debt / 0.7 if total_monthly_debt > 0 else 0
    income_gap = max(required_income - total_monthly_income, 0)

    r1, r2, r3 = st.columns(3)
    r1.metric("每月總負債（含房貸）", f"NT$ {total_monthly_debt:,.0f}")
    r2.metric("通過 70% DTI 所需月收入", f"NT$ {required_income:,.0f}")
    r3.metric(
        "收入缺口",
        f"NT$ {income_gap:,.0f}",
        delta_color="inverse" if income_gap > 0 else "normal",
    )
    if income_gap > 0:
        st.warning(
            f"⚠️ 你還需要每月再多 **NT$ {income_gap:,.0f}** 的收入，"
            "才能讓 DTI 剛好壓在 70% 紅線下。建議拉副業、提高薪資、或縮減房貸總額／延長年限。"
        )
    else:
        st.success("✅ 收入已超過 70% 紅線回推門檻，DTI 安全。")


# ======================================================
# Tab 4：投資收益情境
# ======================================================
with tab_invest:
    st.header("🏠 投資收益情境（含房價增值3情境）")
    st.caption("公式來源：Excel 投資收益計算 — 租金回收率、投資回收期、樂觀/現實/悲觀房價增值。")

    annual_rent = rent * 12
    rental_yield = annual_rent / total_investment if total_investment > 0 else 0
    monthly_net = rent - post_grace_payment
    annual_net = monthly_net * 12
    payback_years = total_investment / annual_net if annual_net > 0 else float("inf")

    i1, i2, i3, i4 = st.columns(4)
    i1.metric("年租金收入", f"NT$ {annual_rent:,.0f}")
    i2.metric("租金收益率", f"{rental_yield * 100:.2f}%")
    i3.metric(
        "月淨現金流",
        f"NT$ {monthly_net:,.0f}",
        delta_color="normal" if monthly_net >= 0 else "inverse",
    )
    i4.metric(
        "投資回收期",
        "無法回收" if payback_years == float("inf") or payback_years < 0
        else f"{payback_years:.1f} 年",
    )

    if monthly_net >= 0:
        st.success(
            f"✅ 月淨收益 +NT$ {monthly_net:,.0f}，房客在幫你付房貸還有剩，標準的『生錢資產』。"
        )
    else:
        st.warning(
            f"⚠️ 月淨現金流 NT$ {monthly_net:,.0f}（為負），"
            "你每月還要倒貼，這是『負現金流物件』，需靠未來增值才有報酬。"
        )

    st.markdown("##### 📈 房價增值 3 情境試算（樂觀 4.5% / 現實 3.0% / 悲觀 2.0%）")
    years_list = [0, 5, 10, 15, 20]
    optimistic = [house_price * (1.045 ** y) for y in years_list]
    realistic = [house_price * (1.03 ** y) for y in years_list]
    pessimistic = [house_price * (1.02 ** y) for y in years_list]

    fig5 = go.Figure()
    fig5.add_trace(
        go.Scatter(
            x=years_list, y=optimistic, mode="lines+markers",
            name="樂觀 +4.5%/年",
            line=dict(color="#27AE60", width=3),
        )
    )
    fig5.add_trace(
        go.Scatter(
            x=years_list, y=realistic, mode="lines+markers",
            name="現實 +3.0%/年",
            line=dict(color="#2980B9", width=3),
        )
    )
    fig5.add_trace(
        go.Scatter(
            x=years_list, y=pessimistic, mode="lines+markers",
            name="悲觀 +2.0%/年",
            line=dict(color="#C0392B", width=3),
        )
    )
    fig5.update_layout(
        xaxis_title="持有年數",
        yaxis_title="預估房價（元）",
        height=420,
        margin=dict(t=20, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig5, use_container_width=True)

    df_price = pd.DataFrame(
        {
            "持有年數": years_list,
            "樂觀(4.5%)": [f"NT$ {v:,.0f}" for v in optimistic],
            "現實(3.0%)": [f"NT$ {v:,.0f}" for v in realistic],
            "悲觀(2.0%)": [f"NT$ {v:,.0f}" for v in pessimistic],
        }
    )
    st.dataframe(df_price, use_container_width=True, hide_index=True)


# ======================================================
# Tab 5：風險壓力測試（利率 + 空租 + 收入下滑）
# ======================================================
with tab_risk:
    st.header("⚠️ 風險壓力測試")
    st.caption("公式來源：Excel 風險管理系統 — 空租準備金、利率衝擊、收入下滑。")

    # 空租風險
    st.markdown("##### 🏚️ 空租風險評估")
    monthly_cost = post_grace_payment + mgmt_fee
    required_vacancy_reserve = vacancy_months * monthly_cost
    reserve_adequacy = (
        cash_reserve / required_vacancy_reserve if required_vacancy_reserve > 0 else float("inf")
    )

    v1, v2, v3 = st.columns(3)
    v1.metric("月總固定成本（房貸+管理費）", f"NT$ {monthly_cost:,.0f}")
    v2.metric("建議空租準備金", f"NT$ {required_vacancy_reserve:,.0f}")
    v3.metric(
        "準備金充足度",
        "∞" if reserve_adequacy == float("inf") else f"{reserve_adequacy * 100:.1f}%",
    )
    if reserve_adequacy >= 1:
        st.success("✅ 現有預備金足以撐過預估空租期。")
    else:
        st.warning(
            f"⚠️ 預備金缺口 NT$ {required_vacancy_reserve - cash_reserve:,.0f}，"
            "建議補強現金存款再進場。"
        )

    # 利率衝擊
    st.markdown("##### 📈 利率衝擊壓力測試（+1% / +2%）")
    base_pay = post_grace_payment
    rate_scenarios = [
        ("目前利率", annual_rate, base_pay, 0),
    ]
    for d in [0.01, 0.02]:
        new_rate = annual_rate + d
        new_pay = pmt(new_rate / 12, pay_months, loan_amount)
        delta = new_pay - base_pay
        rate_scenarios.append((f"利率+{int(d * 100)}%", new_rate, new_pay, delta))

    df_rs = pd.DataFrame(rate_scenarios, columns=["情境", "新利率", "新月付金", "增加金額"])
    df_rs["影響評估"] = df_rs["增加金額"].apply(
        lambda x: "基準" if x == 0 else (
            "✅ 可承受" if x < cf_avg * 0.5 else "⚠️ 警戒"
        )
    )

    fig6 = go.Figure()
    fig6.add_trace(
        go.Bar(
            x=df_rs["情境"],
            y=df_rs["新月付金"],
            marker_color=["#3498DB", "#E67E22", "#C0392B"],
            text=[f"NT$ {v:,.0f}" for v in df_rs["新月付金"]],
            textposition="outside",
        )
    )
    fig6.update_layout(
        yaxis_title="月付金（元）",
        height=360,
        margin=dict(t=20, b=40),
    )
    st.plotly_chart(fig6, use_container_width=True)

    df_rs_display = df_rs.copy()
    df_rs_display["新利率"] = df_rs_display["新利率"].apply(lambda x: f"{x * 100:.2f}%")
    st.dataframe(
        df_rs_display.style.format(
            {"新月付金": "{:,.0f}", "增加金額": "{:,.0f}"}
        ),
        use_container_width=True,
        hide_index=True,
    )

    # 收入下滑情境
    st.markdown("##### 📉 收入下滑情境（-20% / -30%）")
    inc_scenarios = []
    for pct, label in [(1.0, "正常收入"), (0.8, "收入 -20%"), (0.7, "收入 -30%")]:
        new_income = total_monthly_income * pct
        new_cf = new_income - post_grace_payment - monthly_living - monthly_bad_debt
        inc_scenarios.append(
            {
                "情境": label,
                "新月收入": new_income,
                "新月現金流": new_cf,
                "結果": "✅ 安全" if new_cf > 0 else "❌ 入不敷出",
            }
        )
    df_inc = pd.DataFrame(inc_scenarios)

    fig7 = go.Figure()
    fig7.add_trace(
        go.Bar(
            x=df_inc["情境"],
            y=df_inc["新月現金流"],
            marker_color=["#27AE60" if v > 0 else "#C0392B" for v in df_inc["新月現金流"]],
            text=[f"NT$ {v:,.0f}" for v in df_inc["新月現金流"]],
            textposition="outside",
        )
    )
    fig7.add_hline(y=0, line_dash="dash", line_color="red")
    fig7.update_layout(
        yaxis_title="月現金流（元）",
        height=360,
        margin=dict(t=20, b=40),
    )
    st.plotly_chart(fig7, use_container_width=True)
    st.dataframe(
        df_inc.style.format({"新月收入": "{:,.0f}", "新月現金流": "{:,.0f}"}),
        use_container_width=True,
        hide_index=True,
    )


# ======================================================
# Tab 6：租金安全懶人包（1e812 公式）
# ======================================================
with tab_lazy:
    st.header("📋 租金安全懶人包")
    st.caption("公式來源：Excel 懶人包 — 安全指數 = 實拿租金 / 月房貸；底線租金 = 總成本 / (1-折讓)。")

    real_rent = rent * (1 - vacancy_discount)
    repair_fund = rent * repair_pct
    monthly_total_cost_lazy = post_grace_payment + mgmt_fee + repair_fund
    breakeven_rent = (
        monthly_total_cost_lazy / (1 - vacancy_discount) if vacancy_discount < 1 else 0
    )
    safety_index = real_rent / post_grace_payment if post_grace_payment > 0 else 0

    l1, l2, l3 = st.columns(3)
    l1.metric("實拿租金（打折後）", f"NT$ {real_rent:,.0f}")
    l2.metric("月總成本（房貸+開銷+維修）", f"NT$ {monthly_total_cost_lazy:,.0f}")
    l3.metric("底線租金（上架不能低於）", f"NT$ {breakeven_rent:,.0f}")

    st.markdown("##### 🎯 安全指數（≥1.2 才能做，越高越舒服）")

    # Gauge chart
    fig8 = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=safety_index,
            number={"font": {"size": 48}},
            gauge={
                "axis": {"range": [0, 3]},
                "bar": {"color": "#2C3E50"},
                "steps": [
                    {"range": [0, 1.0], "color": "#F5B7B1"},
                    {"range": [1.0, 1.2], "color": "#F9E79F"},
                    {"range": [1.2, 3.0], "color": "#A9DFBF"},
                ],
                "threshold": {
                    "line": {"color": "red", "width": 4},
                    "thickness": 0.8,
                    "value": 1.2,
                },
            },
            title={"text": "安全指數 (Real Rent / 月房貸)"},
        )
    )
    fig8.update_layout(height=320, margin=dict(t=40, b=20))
    st.plotly_chart(fig8, use_container_width=True)

    if safety_index >= 1.2 and rent >= breakeven_rent:
        st.success(
            f"✔ **安全（可上架）** — 安全指數 {safety_index:.2f}（≥1.2），"
            f"且實際租金 NT$ {rent:,.0f} ≥ 底線租金 NT$ {breakeven_rent:,.0f}。"
        )
    elif safety_index >= 1.0:
        st.warning(
            f"△ **偏緊（需要調整）** — 安全指數 {safety_index:.2f}（介於 1.0 ~ 1.19）。"
            "建議：降固定開銷、拉租金、壓房價、加自備款、或談更低利率/更長年限。"
        )
    else:
        st.error(
            f"✗ **危險（不建議買進）** — 安全指數 {safety_index:.2f}（<1.0），"
            "實拿租金連房貸都付不起，每月都要倒貼。"
        )

    st.markdown("---")
    st.info(
        "**怎麼用懶人包：**\n"
        "1. 改側邊欄『租金與投資』裡面四個藍色欄位（月租、管理費、空置折讓、維修比）。\n"
        "2. 看兩個重點：安全指數（≥1.2）+ 底線租金（你的上架價要 ≥ 它）。\n"
        "3. 偏緊或危險時的調整方法：降開銷、拉租金、壓房價、加頭期，或談更低利率/更長年限。"
    )


# ===================== 頁尾 =====================
st.divider()
st.caption(
    "※ 本工具整合自《Ziv學長房地產投資與財富思維》三份實戰試算表，"
    "提供方向性自我檢核；實際銀行核貸條件以各銀行徵授信標準為準。"
)
