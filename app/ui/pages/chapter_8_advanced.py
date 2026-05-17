"""Chapter 8 UI — 奈米級防坑與核彈策略（重構後）。

UI 層：純 widgets + 渲染；合約地雷 + 謄本地雷由 services.presale_filter，
空租準備金由 services.leverage。文案銀行 / SOP 純 markdown 留 UI 層。
"""

from __future__ import annotations

import streamlit as st

from app.services.leverage import calculate_vacancy_reserve
from app.services.presale_filter import (
    diagnose_contract_landmines,
    diagnose_title_deed,
)


# ===== 預售屋合約陷阱（Ch.8 自己的 4 條，與 Ch.2 不同清單）=====
PRESALE_TRAP_CLAUSES: list[tuple[str, str]] = [
    ("① 建商要求支付『天然瓦斯、自來水／電管線與道路開挖費』", "ch8_presale_utility_fee"),
    ("② 車位合約僅標示長、寬，**未標示『高度』**", "ch8_presale_parking_height"),
    ("③ 附屬建物將『雨遮／屋簷』計入買賣價格", "ch8_presale_eaves"),
    ("④ 履約保證的『價金返還保證費』要求買方支付", "ch8_presale_guarantee_fee"),
]

# 中古屋謄本兩大地雷
RESALE_LANDMINE_GROUND = ("① 土地項目為『空白』（無土地持分）", "ch8_resale_no_land")
RESALE_LANDMINE_PRIVATE = ("② 他項權利設定有『私人（自然人）』", "ch8_resale_private_lien")

# 地段等級顯示
LOCATION_LABEL_MAP: dict[int, str] = {
    1: "1 級｜極精華（雙北捷運站旁／信義內科）",
    2: "2 級｜次精華（六都市中心、學區外圍）",
    3: "3 級｜一般市區（縣市政府周邊）",
    4: "4 級｜重劃區／市郊（生活機能尚可）",
    5: "5 級｜極偏遠（鄉鎮、無捷運／工作圈外）",
}

CREDIT_PENALTY_OPTIONS: list[str] = [
    "信用卡只繳最低（產生循環利息）",
    "欠繳電話費／罰單超過 2 萬元",
    "工作年資未滿一年（含換工作未滿一年）",
    "我是『信用小白』（從未辦過信用卡）",
]

NEGOTIATION_SOP_CHECKS: list[tuple[str, str]] = [
    ("① 是否已打聽『賣多久了』以及『是否為一般約』？", "ch8_sop_listing_age"),
    ("② 驗屋是否帶了『小夜燈』測插座、『衛生紙』測洗手台下 P 管漏水？",
     "ch8_sop_inspection_tools"),
    ("③ 是否帶水平尺測量牆角為完美的『90 度』？", "ch8_sop_level_check"),
]

COPYWRITING_BANK: dict[str, str] = {
    "🎓 學生（首次離家、預算敏感）": (
        "**❌ 不要寫：**「便宜出租、近學校、家具齊全」——學生看一百間都是這句。\n\n"
        "**✅ 學長版文案：**\n"
        "> 「月租 9K = **每天 300 元 = 一頓晚餐錢**。\n"
        "> 24 小時管理員、刷卡進出、**爸媽最放心**。\n"
        "> 走路 7 分鐘到校門口，下雨不用追公車。」\n\n"
        "**🎯 心理戰要點：** 把月租切成『每天』，再對比『一頓晚餐』——"
        "讓爸媽（真正付錢的人）覺得超划算；加上『安全』兩個字，"
        "媽媽就會直接幫小孩簽約。"
    ),
    "👨‍👩‍👧 小家庭（首購／換屋、孩子是命脈）": (
        "**❌ 不要寫：**「三房兩廳、近捷運、明亮通風」——小家庭根本不在乎這些。\n\n"
        "**✅ 學長版文案：**\n"
        "> 「**省下的頭期款，就是孩子的才藝基金。**\n"
        "> 走路 5 分鐘到 ⭐ 明星國小，下課自己回家不用接送。\n"
        "> 樓下就是公園 + 全聯，假日全家走路採買零負擔。」\n\n"
        "**🎯 心理戰要點：** 小家庭的決策權在『媽媽』，"
        "媽媽的決策中心是『小孩』。把房子的價值翻譯成『對小孩的好處』，"
        "再順便戳一下『接送的痛點』，秒簽。"
    ),
    "💼 高階上班族（時間就是錢、要面子）": (
        "**❌ 不要寫：**「電梯華廈、新裝潢、可短租」——這些是基本盤，沒有差異化。\n\n"
        "**✅ 學長版文案：**\n"
        "> 「捷運站走路 **3 分鐘**，上班通勤多睡 30 分。\n"
        "> 一樓管理員 **24 小時代收網購、生鮮、文件**。\n"
        "> 開放式中島 + 高速光纖，**在家處理工作的效率加倍**，\n"
        "> 下班直接回到自己的『充電基地』。」\n\n"
        "**🎯 心理戰要點：** 高階上班族不缺錢，缺的是『時間』與『歸屬感』。"
        "把房子包裝成『效率工具 + 充電基地』，租金多 3K 他也覺得值。"
    ),
}


def _render_contract_defense_tab() -> None:
    st.subheader("🛡️ 合約與產權絕對防禦網")
    st.caption("學長心法：『契約只看一次，但坑會跟你一輩子。』")

    # 預售屋合約快篩 — 用 presale_filter service
    st.markdown("##### 🏗️ 預售屋合約違法／陷阱條款快篩")
    st.caption("以下任何一項勾選，都是建商在『偷錢』或『規避法規』！")

    presale_hits = tuple(st.checkbox(label, key=key) for label, key in PRESALE_TRAP_CLAUSES)
    presale_verdict = diagnose_contract_landmines(presale_hits)

    if presale_verdict.has_any_landmine:
        st.error(
            f"⚠️ **抓到 {presale_verdict.landmine_count} 條違法／陷阱條款！**\n\n"
            "**內政部定型化契約**早就明定這些費用**由建商負擔**或**禁止計價**：\n"
            "- 管線開挖費 → 建商成本，不可轉嫁\n"
            "- 車位只標長寬不標高 → 之後休旅車進不來算誰的？\n"
            "- 雨遮計價 → 105 年後新案**完全禁止**，舊案也不可登記面積\n"
            "- 履保費 → **建商義務**，要買方付就是吃定你不懂\n\n"
            "👉 **學長動作清單：**\n"
            "1. 立刻書面要求建商修改條款\n"
            "2. 不改？直接打 **1950 消保官** 或內政部檢舉\n"
            "3. 全部沒談妥前，**不要交任何訂金**！"
        )
    else:
        st.success("✅ 目前條款乾淨，但簽約前請再請代書／律師複核一次。")

    st.markdown("---")

    # 中古屋謄本兩大地雷 — 用 presale_filter service
    st.markdown("##### 🏘️ 中古屋謄本排雷")
    st.caption("謄本一張 20 元，但能幫你看穿一輩子最大的陷阱。")

    no_land = st.checkbox(RESALE_LANDMINE_GROUND[0], key=RESALE_LANDMINE_GROUND[1])
    private_lien = st.checkbox(RESALE_LANDMINE_PRIVATE[0], key=RESALE_LANDMINE_PRIVATE[1])
    deed = diagnose_title_deed(no_land, private_lien)

    if deed.no_land:
        st.error(
            "🚫 **致命地雷：地上權住宅！**\n\n"
            "土地欄空白＝你買的只是『使用權』，**沒有土地產權**。\n"
            "- 銀行貸款成數低（通常 5 成）、年期短（最多 20 年）\n"
            "- 70 年到期就要還給地主／政府，房子**歸零**\n"
            "- 二手轉手極難，房價漲不動\n\n"
            "👉 **學長判斷：除非你只想『便宜租 70 年』，否則直接放棄。**"
        )
    if deed.private_lien:
        st.error(
            "🚫 **黑道地雷：私人他項權利！**\n\n"
            "他項權利的權利人是『自然人（私人姓名）』而非銀行——"
            "**幾乎可以斷定是民間高利貸或地下錢莊**。\n"
            "- 過戶時可能被假扣押\n"
            "- 屋主可能正在跑路，賣完就消失\n"
            "- 黑道追討會找上**新屋主（你）**\n\n"
            "👉 **學長動作：立刻放棄此案，連訂金都不要付！**"
        )
    if not deed.has_any_landmine:
        st.info("🟢 兩大地雷皆未踩中，可進入下一階段：實地看屋 + 鄰居打聽。")


def _render_finance_risk_tab() -> None:
    st.subheader("💰 高階財務與風控計算機")
    st.caption("學長心法：『會賺錢的是英雄，撐得住空租的才是贏家。』")

    # 空租準備金 — 用 leverage service
    st.markdown("##### 🦢 空租準備金與黑天鵝風控")

    col_a, col_b = st.columns(2)
    with col_a:
        location_level = st.selectbox(
            "房屋地段等級",
            options=list(LOCATION_LABEL_MAP.keys()),
            format_func=lambda lvl: LOCATION_LABEL_MAP[lvl],
            index=2, key="ch8_location_level",
        )
    with col_b:
        monthly_fixed_cost = st.number_input(
            "每月固定支出（房貸 + 管理費，元）", min_value=0, value=30_000, step=1_000,
            help="本利攤還的月付金 + 管委會月費 + 房屋稅／地價稅平均月攤。",
            key="ch8_monthly_cost",
        )

    reserve = calculate_vacancy_reserve(int(location_level), int(monthly_fixed_cost))

    st.markdown("---")
    m1, m2, m3 = st.columns(3)
    m1.metric("預估空租月數", f"{reserve.estimated_vacancy_months} 個月")
    m2.metric("每月固定支出", f"{monthly_fixed_cost:,.0f} 元")
    m3.metric(
        "🛡️ 絕對防禦金（必備）", f"{reserve.emergency_fund_ntd:,.0f} 元",
        delta=f"≈ {reserve.emergency_fund_ntd / 10_000:,.1f} 萬",
        help="這是讓你『不會被斷頭』的底線。",
    )

    st.info(
        "💡 **這筆錢必須死守在戶頭！**\n\n"
        "它不是拿來消費的——這是你抵禦**升息**與**空租黑天鵝**的保命底線。\n"
        "建議放在**獨立戶頭**、不綁定信用卡扣款、不買股票不買基金。\n"
        "**寧可少賺 0.5% 利息，也不要在升息那天才在賣股票補繳房貸。**"
    )

    st.markdown("---")

    # 隱形聯徵扣分（純 UI，無 service 邏輯）
    st.markdown("##### 🔍 隱形聯徵扣分檢測")
    st.caption("這些事銀行不會講，但會悄悄把你的房貸成數砍掉。")

    selected_penalties = st.multiselect(
        "請勾選你目前『中』的項目（誠實面對自己）",
        options=CREDIT_PENALTY_OPTIONS,
        key="ch8_credit_penalties",
    )

    if selected_penalties:
        st.warning(
            f"🟠 **警告：你中了 {len(selected_penalties)} 個聯徵扣分項！**\n\n"
            + "\n".join(f"- ❌ {p}" for p in selected_penalties)
            + "\n\n**這些都會讓你的房貸成數被大砍 5%~15%、或利率被加 0.25%~0.5%！**\n\n"
            "👉 **學長急救清單：**\n"
            "1. 信用卡循環利息：**立刻全額繳清**，連續 3 個月不要再用循環\n"
            "2. 罰單／電話費：**全部繳清**，並等聯徵更新（約 1 個月）\n"
            "3. 工作年資不足：**先別跳槽**，撐滿 1 年再申請房貸\n"
            "4. 信用小白：**現在就辦一張信用卡**，每月小額消費全額繳清養信用\n\n"
            "**聯徵分數要養 6 個月才看得到效果，現在不動，半年後哭著加自備款。**"
        )
    else:
        st.success("✅ 聯徵狀況乾淨，可全力衝刺爭取最高成數！")


def _render_psychology_tab() -> None:
    st.subheader("🧠 心理戰與行銷兵器庫")
    st.caption("學長心法：『成交不是靠話術，是靠你比對方更懂他自己。』")

    # 看屋 SOP（純 UI checkbox 計數，無 service 邏輯需要）
    st.markdown("##### 🕵️ 看屋談判情報收集 SOP")
    st.caption("沒做這三件事就出價的，都是建商／房仲眼中的肥羊。")

    sop_results = [st.checkbox(label, key=key) for label, key in NEGOTIATION_SOP_CHECKS]
    completed = sum(sop_results)
    total = len(NEGOTIATION_SOP_CHECKS)
    st.progress(completed / total)
    st.caption(f"情報完整度：**{completed} / {total}**")

    if completed == total:
        st.success(
            "✅ **三項情報全收齊！** 現在你才有資格出價。\n\n"
            "- 賣超過 3 個月 → 屋主已疲乏，可砍 8~12%\n"
            "- 一般約 → 仲介有空間幫你橋\n"
            "- 驗屋三神器發現問題 → **每一項都是殺價籌碼**"
        )
    elif completed >= 1:
        st.warning(
            f"🟡 還缺 {total - completed} 項情報就出價，等於**蒙著眼睛跟賣方對賭**。"
        )
    else:
        st.error(
            "🚫 一項都沒做就要出價？學長直接攔住你——**現在出去等於把錢丟水裡**。"
        )

    st.markdown("---")

    # 爆款文案（純文案 lookup，留 UI 層）
    st.markdown("##### ✍️ 爆款文案生成器（出租用）")
    st.caption("同一間房，文案寫對人，租金可以差 2K～5K。")

    target_audience = st.selectbox(
        "選擇你的目標客群",
        options=list(COPYWRITING_BANK.keys()),
        index=0,
        key="ch8_target_audience",
    )

    st.markdown("---")
    st.markdown(f"##### 💎 {target_audience} 專屬學長文案")
    st.markdown(COPYWRITING_BANK[target_audience])


def render_chapter_8() -> None:
    """🔥 奈米級防坑與核彈策略（Chapter 8）— UI 入口。"""
    st.title("🔥 奈米級防坑與核彈策略")
    st.info(
        "💡 **學長的實戰金句**：「**新手怕買不到，老手怕買錯**。\n"
        "前 7 章教你怎麼進場，這一章教你怎麼**不被抬出場**——"
        "每一個小細節，都是別人付了幾百萬學費換來的血淚。」"
    )

    tab_contract, tab_finance, tab_psych = st.tabs(
        ["🛡️ 合約與產權絕對防禦網", "💰 高階財務與風控計算機", "🧠 心理戰與行銷兵器庫"]
    )

    with tab_contract:
        _render_contract_defense_tab()
    with tab_finance:
        _render_finance_risk_tab()
    with tab_psych:
        _render_psychology_tab()
