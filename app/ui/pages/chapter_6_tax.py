"""Chapter 6 UI — 節稅護城河與富豪隱形槓桿（重構後）。

UI 層：純 widgets + 渲染；裝潢分類由 services.tax，股票質押由 services.leverage。
重購退稅章節為純知識文字（無計算邏輯），直接放在 UI 層。
"""

from __future__ import annotations

import streamlit as st

from app.models.constants import STOCK_PLEDGE_ANNUAL_RATE, STOCK_PLEDGE_LTV
from app.services.leverage import calculate_stock_pledge
from app.services.tax import RENOVATION_OPTIONS, classify_renovation_items


def _render_renovation_whitelist() -> None:
    st.markdown("### 🏛️ 區塊一：國稅局裝潢抵稅白名單")
    st.caption("學長心法：『**裝潢報得對，賣房省百萬；報得錯，被罰更心痛。**』")

    st.info(
        "📚 **背景知識**：房地合一稅 2.0 計算「財產交易所得」時，"
        "**已支付且可舉證的裝潢費**可從售屋利潤中扣除。\n\n"
        "但**國稅局有明確分類**——『屬於房屋本體的固定裝修』才能抵，"
        "『可拆卸搬走的家具家電』一律不認！"
    )

    selected_items = st.multiselect(
        "請勾選你『預計申報抵稅』的裝潢項目",
        options=list(RENOVATION_OPTIONS),
        default=[],
        help="搬家時帶得走的東西，國稅局都不認。",
        key="ch6_renovation_items",
    )
    verdict = classify_renovation_items(tuple(selected_items))

    st.markdown("---")
    m1, m2, m3 = st.columns(3)
    m1.metric("已勾選項目", f"{len(selected_items)} 項")
    m2.metric("✅ 可抵稅", f"{len(verdict.allowed_items)} 項")
    m3.metric(
        "❌ 國稅局禁區", f"{len(verdict.forbidden_items)} 項",
        delta_color="inverse",
    )

    if verdict.has_forbidden:
        st.error(
            f"❌ **剔除並罰款！** 你勾選的 **{len(verdict.forbidden_items)} 項**屬於"
            "**『可移動物品』**，國稅局**絕對不認列**：\n\n"
            + "\n".join(f"- 🚫 **{item}**" for item in verdict.forbidden_items)
            + "\n\n---\n\n"
            "**為什麼不認？** 因為搬家時你可以**直接抱走**——"
            "這是『**家具**』不是『**房屋本體裝修**』。國稅局的判定原則：\n"
            "- 釘死／焊死／灌漿 → ✅ 屬於房屋一部分\n"
            "- 螺絲拆卸即可帶走 → ❌ 屬於動產（家具家電）\n\n"
            "👉 **學長提醒**：硬報這些項目，輕則剔除，**重則被罰漏報稅額 0.5 倍**。"
            "申報前**自行先剔除**才是上策。"
        )

    if verdict.allowed_items:
        st.success(
            f"✅ **可抵稅 {len(verdict.allowed_items)} 項：**\n\n"
            + "\n".join(f"- ✔️ {item}" for item in verdict.allowed_items)
            + "\n\n這些項目屬於『**不可拆卸的固定裝修**』，"
            "**只要證據齊全**就可從售屋所得中扣除，**節稅效果可達數十萬到上百萬**。"
        )

    st.info(
        "💡 **必備鐵證清單（少一樣都會被打回票）：**\n\n"
        "1. **發票一定要有『廠商統編』**——個人開的收據完全沒用\n"
        "2. **絕對不能忘記拍『修繕前後對照照片』**——證明真的有做工程\n"
        "3. **付款紀錄**——刷卡單／轉帳明細，不要付現金\n"
        "4. **工程合約書**——含項目、單價、總價、工期\n"
        "5. **完工驗收單**或里長見證\n\n"
        "**沒有以上證據，再多裝潢費都會被視為『逃漏稅』，反過來被加罰！**"
    )


def _render_vip_leverage() -> None:
    st.markdown("### 💎 區塊二：VIP 富豪隱形槓桿模擬器")
    st.caption("學長心法：『**有錢人不是錢比你多，是『繞道借錢』的本事比你多。**』")

    st.markdown("##### 📈 股票質押免吃 DTI 試算")
    st.caption("為什麼有錢人可以一直買房？因為他們**借的錢不會出現在房貸聯徵上**。")

    stock_market_value = st.number_input(
        "持有的 0050 / 台積電 股票市值（元）",
        min_value=0, value=10_000_000, step=500_000,
        help="你目前可用來質押的優質藍籌股市值。一般銀行只認 0050、台積電、金融股等大型權值股。",
        key="ch6_stock_value",
    )

    result = calculate_stock_pledge(float(stock_market_value))

    st.markdown("---")
    m1, m2, m3 = st.columns(3)
    m1.metric(
        "可質押金額", f"{result.pledgeable_amount_ntd:,.0f} 元",
        delta=f"≈ {result.pledgeable_amount_ntd / 10_000:,.0f} 萬",
        help=f"市值 × {STOCK_PLEDGE_LTV * 100:.0f}% 質押成數。",
    )
    m2.metric(
        "年利率", f"{STOCK_PLEDGE_ANNUAL_RATE * 100:.1f}%",
        help="一般優於信貸（5-7%），略低於房貸（2%）。",
    )
    m3.metric(
        "每月利息", f"{result.monthly_interest_ntd:,.0f} 元",
        delta=f"年息 {result.annual_interest_ntd:,.0f} 元",
        delta_color="inverse",
    )

    if result.pledgeable_amount_ntd > 0:
        st.success(
            "🚀 **這筆借出來的錢叫『證券週轉金』——**\n\n"
            f"它**完全不會出現在你的房貸聯徵上**，更不會吃掉你的 DTI（總負債比）。\n\n"
            f"**白話翻譯：你的房貸成數一點都不會被影響**——\n"
            f"你的 **{result.pledgeable_amount_ntd / 10_000:,.0f} 萬**就這樣『**無中生有**』，"
            "可以拿去當下一間房的自備款！\n\n"
            "👉 **這就是政商名流『無中生有買第二間房』的終極密技：**\n"
            "1. 把現金部位**全壓 0050 / 台積電**（領股息＋資本利得）\n"
            "2. 需要錢時**質押 60%**借出『證券週轉金』\n"
            "3. **用週轉金當第二間房的頭期款**（聯徵看不到）\n"
            "4. 第二間房**全額用購屋貸款**（科目一最低利率）\n"
            "5. 收租 / 增值雙頭賺，股票配息照領\n\n"
            "**唯一風險：股票崩盤需補保證金。所以只能押權值股 + 留 30% 緩衝。**"
        )

    st.markdown("---")
    st.markdown("##### 🏰 學長的『富豪護城河』知識庫")
    st.caption("這些工具一般人聽都沒聽過——但每個老闆背後都在用。")

    with st.expander("🏢 **為何大老闆愛用『閉鎖型公司』買商辦？**（股權轉讓避稅）"):
        st.markdown(
            "#### 閉鎖型股份有限公司 × 房地產三大魔法\n\n"
            "**1️⃣ 股權轉讓 ≠ 不動產轉讓 → 免房地合一稅**\n"
            "- 一般人賣房子要繳 **房地合一稅 35%~45%**\n"
            "- 但如果房子掛在**公司名下**，賣『**公司股權**』給買家，"
            "**公司資產（房子）沒有轉手，只是股東換人**\n"
            "- 證券交易所得課稅目前**停徵**——直接**省下幾百萬稅金**\n\n"
            "**2️⃣ 多人持有不公開 → 規避奢侈稅與閒置追稅**\n"
            "- 閉鎖型公司**不必揭露股東名冊**\n"
            "- 政府要查『誰持有第 N 戶』查不到——**避開特定身分加重稅**\n\n"
            "**3️⃣ 公司費用列支 → 裝潢、利息、管理費全可抵稅**\n"
            "- 個人裝潢只能在賣房時抵\n"
            "- **公司每年都可以列費用**抵營利事業所得稅\n\n"
            "**⚠️ 學長警告**：適用條件嚴格——**至少需 3 人股東、設立成本約 5-10 萬、"
            "每年會計師簽證費 3-8 萬**。資產 < 5,000 萬玩這個會划不來。"
        )

    with st.expander("🛡️ **為何要用『他益信託』？**（債主無法查封法拍）"):
        st.markdown(
            "#### 他益信託 × 資產防火牆\n\n"
            "**什麼是他益信託？**\n"
            "- **委託人**（你）把資產（房子、股票）**信託給銀行**\n"
            "- **受益人指定為『他人』**（通常是子女或配偶）\n"
            "- 資產所有權**從你身上脫離**，移轉到信託架構\n\n"
            "**為什麼有錢人都在做？**\n\n"
            "**1️⃣ 防債主查封 / 法拍**\n"
            "- 信託後的資產**不屬於委託人個人財產**\n"
            "- 即使你經營公司倒了、被告求償，**債主也無法強制執行信託內的資產**\n"
            "- **連離婚分產也碰不到**（信託成立後超過 5 年的資產，不列入夫妻財產）\n\n"
            "**2️⃣ 二代傳承 + 提前贈與**\n"
            "- 信託期間每年可享**贈與稅免稅額 244 萬**\n"
            "- **分年贈與**，總額可省下大筆遺產稅\n"
            "- 受益人**未成年也能繼承**，由銀行代管\n\n"
            "**3️⃣ 控制權與所有權分離**\n"
            "- 房子在子女名下（受益人），但**子女不能擅自賣掉**（信託合約規範）\n"
            "- 等於『**給他財富，但不給他敗光的權力**』\n\n"
            "**⚠️ 學長警告**：設立信託要付**信託管理費**（每年資產的 0.3-0.5%），"
            "而且**5 年內被認定脫產仍可被追討**——要早做、要正規做。"
        )

    with st.expander("💰 **Bonus：『重購退稅』學長解法**（一般人最容易忽略）"):
        st.markdown(
            "#### 重購退稅 × 換屋不繳稅\n\n"
            "**規則**：賣舊房 + 2 年內買新房（且金額 ≥ 舊房售價），"
            "已繳的『**房地合一稅**』可**全額退還**或**抵免**。\n\n"
            "**學長操作順序：**\n"
            "1. **先賣後買**：賣舊房先繳稅 → 2 年內買新房 → 退稅\n"
            "2. **先買後賣**：先買新房 → 2 年內賣舊房 → 抵免新繳稅額\n\n"
            "**關鍵眉角：**\n"
            "- 新舊房**都必須是自用住宅**（本人或直系設籍 + 無出租）\n"
            "- 新房**價格 ≥ 舊房售價**才能全額退\n"
            "- 退稅後**新房需設籍滿 5 年**，否則要追繳\n\n"
            "**這條規定可以讓你『**換大房不繳房地合一稅**』，等於資產自由升級！**"
        )


def render_chapter_6() -> None:
    """🛡️ 節稅護城河與裝潢抵稅清單（Chapter 6）— UI 入口。"""
    st.title("🛡️ 節稅護城河與裝潢抵稅清單")
    st.info(
        "💡 **學長的實戰金句**：「**合法節稅不是逃稅，是知道規則的人才有的紅利。**\n"
        "每一筆裝潢都該留發票——未來賣房時，這就是你抵稅的盔甲。\n"
        "**富人比你多賺的不是錢，是『繞道』的本事。**」"
    )

    _render_renovation_whitelist()
    st.markdown("---")
    _render_vip_leverage()
