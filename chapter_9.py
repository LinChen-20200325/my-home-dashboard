"""Chapter 9：學長 AI 實戰顧問（OpenAI 即時對話介面）

獨立模組：提供 render_chapter_9_ai() 函式。

    from chapter_9 import render_chapter_9_ai
    render_chapter_9_ai()

需求：
    - requirements.txt 須包含 `openai>=1.0`
    - API Key 可從 st.secrets["OPENAI_API_KEY"] 讀取，或由側邊欄即時輸入
"""

from __future__ import annotations

from typing import Iterator

import streamlit as st


# ===== 學長系統提示語（內化團隊鐵律）=====
MENTOR_SYSTEM_PROMPT = """你是台灣頂尖的房地產投資實戰教練「學長」。
你的任務是協助學弟妹（使用者）進行買房策略評估、合約防坑、貸款精算與資產翻倍計畫。
你的語氣必須：**犀利、直指核心、充滿自信、用數據與法規說話**。
你極度厭惡「中產階級的消耗性負債（如買車）」，並且極度保護學弟妹不被建商、房仲或銀行坑殺。

# 核心實戰資料庫（你必須嚴格遵守的鐵律，絕不可使用坊間籠統建議）

## 1. 財富思維與總經
- 房價上漲的燃料是 M2 貨幣供給額。買房是利用低息房貸（好債），讓通膨幫你還債。
- 絕對禁止「中產階級毒藥」：車子、自用大房是消耗現金流的負債；能產生租金正現金流的才是資產。
- 資金配置採「槓鈴策略」：80% 防禦（房地產 / 0050 / 美債），20% 攻擊（期貨 / 加密貨幣），不碰中等風險。

## 2. 預售屋防坑鐵律
- 【履約保證】唯一首選「價金返還保證」。極度危險地雷為「同業連帶擔保」。
- 【合約法規】審閱期至少 5 日；附屬建物除陽台外（雨遮 / 屋簷）絕對不可計價；面積誤差 > 3% 可直接退屋；
  延遲交屋每日賠償萬分之五；瓦斯 / 自來水外管費**必由建商負擔**。
- 【圖面篩選】梯戶比黃金標準為 1:4。拒絕高昂公設陷阱（如無邊際游泳池）。

## 3. 中古屋淘金與流動性
- 【出價底線】絕對不可低於「屋主買入本金 + 剩餘貸款價」。
- 【流動性死線】RC 結構耐用 50 年，最晚必須在「**屋齡 35 年前**」脫手。
- 【三大不碰】921（1999 年）以前的房子、40 年老公寓的 4 / 5 樓（健身公寓）、山區豪宅。
- 【銀行拒貸地雷】小於 15 坪、海砂 / 輻射 / 事故 / 傾斜 / 地上權、土地分區為農業區 / 保護區。

## 4. 貸款與金流極限（科目四洗白術）
- 【貸款雙紅線】總貸款負擔率（DTI）必須 < 70%；年紀 + 貸款年限 必須 < 65~75。
- 【財力無敵星】總資產負債比 > 1.5 倍；9A / 9B 所得可拿年度清單並免扣 2.11% 二代健保。
- 【金流過水 SOP】用科目四（增貸）借出的錢，必須：
    1. 轉至他行定存 3 個月
    2. 投入 0050 / 保單留存對帳單鐵證
    3. **放滿 1 年以上**洗白
    4. 才能轉回科目一買下一間房
  **絕對禁止未滿一年買房或夫妻互轉**。

## 5. 出租與稅務護城河
- 【招租文案】必須有具體算式與痛點（例：月租 9K = 每天 300 = 一頓晚餐；省下頭期款當教育基金）。
- 【裝潢抵稅】只有「**固定且不可拆除**」（如泥作、水管、防水）可抵稅。系統家具 / 家電絕對不可。
  發票必須有**統編**，且必備「**修繕前後對照照片**」。
- 【VIP 隱形槓桿】利用「股票質押（不吃 DTI 額度）」借錢，或用「**閉鎖型投資公司**」買商辦轉讓股權避稅。

# 行動指南
1. 當使用者給出收入與負債時，立刻幫他計算 DTI；若 > 70% 或有雙卡循環利息、百元提領紀錄，**立刻嚴厲警告**。
2. 當使用者詢問某個建案能不能買時，要求他提供「建商資本額（需 > 2 億）、履約保證種類、梯戶比、周邊 1 公里嫌惡設施」。
3. 當使用者遇到糾紛（如建商偷換同級品、面積縮水），立刻搬出《預售屋定型化契約應記載及不得記載事項》的法規底線教他談判。
4. **每一段回答的結尾，請附上一句簡短的『學長實戰金句』來強化信心**。

# 風格守則
- 用「學弟」「學妹」稱呼對方，營造輔導感。
- 段落分明、條列重點；不講空話、不打官腔。
- 數據用粗體標示；法規條號要寫清楚。
- 遇到對方明顯要踩雷的決定，**直接喝止**：『學弟，攔住！這一步走下去你會慘賠。』"""


# ===== 模型選項（OpenAI 公開 chat model）=====
MODEL_OPTIONS: list[str] = ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"]
DEFAULT_MODEL = "gpt-4o-mini"

# ===== 起手式問題（給使用者一鍵發問）=====
STARTER_QUESTIONS: list[str] = [
    "學長，建商要我支付天然瓦斯與自來水管線費，這合理嗎？",
    "我月薪 6 萬、有車貸 1.2 萬，買得起 2,000 萬的房子嗎？",
    "新北中和某預售案『同業連帶擔保』履保，可以買嗎？",
    "謄本他項權利部寫了一個私人姓名，這代表什麼？",
    "我想用科目四洗白資金，學長能幫我擬時間軸嗎？",
    "屋齡 32 年的公寓 4 樓，學長覺得能進場嗎？",
]


def _resolve_api_key() -> str | None:
    """優先讀 st.secrets，否則回傳側邊欄輸入值。"""
    try:
        if "OPENAI_API_KEY" in st.secrets:  # type: ignore[operator]
            return str(st.secrets["OPENAI_API_KEY"]).strip() or None
    except Exception:
        # 沒有 secrets.toml 也不報錯
        pass
    return (st.session_state.get("ch9_api_key_input") or "").strip() or None


def _stream_chat_completion(
    client,
    model: str,
    messages: list[dict],
    temperature: float,
) -> Iterator[str]:
    """OpenAI 串流回應，逐塊 yield 內容字串。"""
    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        stream=True,
    )
    for chunk in stream:
        try:
            delta = chunk.choices[0].delta.content
        except (IndexError, AttributeError):
            delta = None
        if delta:
            yield delta


def _render_sidebar_controls() -> tuple[str | None, str, float]:
    """設定面板：API Key、模型、temperature。回傳 (api_key, model, temperature)。"""
    with st.expander("⚙️ **AI 顧問設定**（API Key / 模型 / 創意度）", expanded=False):
        st.text_input(
            "🔑 OpenAI API Key",
            type="password",
            placeholder="sk-...（或設定於 .streamlit/secrets.toml）",
            help="不會儲存到伺服器，只在當前 session 使用。建議部署時改用 st.secrets。",
            key="ch9_api_key_input",
        )

        col_m, col_t = st.columns(2)
        with col_m:
            model = st.selectbox(
                "AI 模型",
                options=MODEL_OPTIONS,
                index=MODEL_OPTIONS.index(DEFAULT_MODEL),
                help="gpt-4o-mini 經濟快速；gpt-4o 回答最深入。",
                key="ch9_model",
            )
        with col_t:
            temperature = st.slider(
                "創意度（temperature）",
                min_value=0.0,
                max_value=1.5,
                value=0.7,
                step=0.1,
                help="低 = 嚴謹引用法規；高 = 更靈活的學長口氣。建議 0.5-0.9。",
                key="ch9_temperature",
            )

        if st.button("🧹 清空對話歷史", use_container_width=True, key="ch9_clear"):
            st.session_state.ch9_messages = []
            st.rerun()

    return _resolve_api_key(), model, temperature


def _render_starter_chips() -> None:
    """顯示快速提問按鈕（首次進入或對話清空時）。"""
    st.caption("💡 **不知道從哪問起？點下面任一題快速開場：**")
    cols = st.columns(2)
    for idx, question in enumerate(STARTER_QUESTIONS):
        target_col = cols[idx % 2]
        with target_col:
            if st.button(
                question,
                key=f"ch9_starter_{idx}",
                use_container_width=True,
            ):
                st.session_state.ch9_pending_input = question
                st.rerun()


def render_chapter_9_ai() -> None:
    """🤖 學長 AI 實戰顧問（Chapter 9）

    使用 OpenAI Chat Completions API + 串流回應，搭載 學長專屬系統提示語，
    讓使用者可即時諮詢看房 / 議價 / 貸款 / 稅務問題。
    """
    st.title("🤖 學長 AI 實戰顧問")
    st.caption(
        "🛡️ 內建學長團隊鐵律 × OpenAI GPT 引擎｜"
        "建商坑你的合約、房仲的話術、銀行不會講的眉角——**問就對了**。"
    )

    # ----- 依賴檢查 -----
    try:
        from openai import OpenAI
    except ImportError:
        st.error(
            "🚫 **未安裝 `openai` 套件**——請在終端機執行：\n\n"
            "```bash\npip install openai>=1.0\n```\n\n"
            "或將 `openai>=1.0` 加入 `requirements.txt` 後重啟服務。"
        )
        return

    # ----- 設定面板 -----
    api_key, model, temperature = _render_sidebar_controls()

    # ----- session_state 初始化 -----
    if "ch9_messages" not in st.session_state:
        st.session_state.ch9_messages: list[dict] = []
    if "ch9_pending_input" not in st.session_state:
        st.session_state.ch9_pending_input: str | None = None

    # ----- API Key 缺失警告 -----
    if not api_key:
        st.warning(
            "🔑 **請先在上方設定區填入 OpenAI API Key**，或於部署環境設定 "
            "`.streamlit/secrets.toml`：\n\n"
            "```toml\nOPENAI_API_KEY = \"sk-...\"\n```"
        )

    st.markdown("---")

    # ----- 對話歷史渲染 -----
    if not st.session_state.ch9_messages:
        _render_starter_chips()
    else:
        for msg in st.session_state.ch9_messages:
            avatar = "🧑‍🎓" if msg["role"] == "user" else "🎓"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

    # ----- 取得使用者輸入：來自 chat_input 或 starter 點擊 -----
    user_input = st.chat_input(
        "輸入你的問題（例：學長，建商要我付瓦斯管線費怎麼辦？）",
        disabled=not api_key,
        key="ch9_chat_input",
    )
    if st.session_state.ch9_pending_input:
        user_input = st.session_state.ch9_pending_input
        st.session_state.ch9_pending_input = None

    if not user_input:
        return

    # ----- 顯示使用者訊息 -----
    st.session_state.ch9_messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="🧑‍🎓"):
        st.markdown(user_input)

    # ----- 呼叫 OpenAI 並串流回應 -----
    try:
        client = OpenAI(api_key=api_key)
        api_messages = [{"role": "system", "content": MENTOR_SYSTEM_PROMPT}] + [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.ch9_messages
        ]

        with st.chat_message("assistant", avatar="🎓"):
            with st.spinner("學長思考中…"):
                response_text = st.write_stream(
                    _stream_chat_completion(client, model, api_messages, temperature)
                )

        st.session_state.ch9_messages.append(
            {"role": "assistant", "content": response_text}
        )
    except Exception as exc:  # noqa: BLE001 — 對使用者轉譯任何 SDK 例外
        with st.chat_message("assistant", avatar="⚠️"):
            st.error(
                f"❌ **AI 服務呼叫失敗**：{type(exc).__name__}\n\n"
                f"```\n{exc}\n```\n\n"
                "請檢查 API Key 是否正確、額度是否足夠、或選用另一個模型重試。"
            )
        # 失敗訊息不寫入歷史，避免污染下次對話 context
        st.session_state.ch9_messages.pop()


# 允許 `streamlit run chapter_9.py` 直接預覽此單一模組
if __name__ == "__main__":
    st.set_page_config(
        page_title="Ch.9 學長 AI 實戰顧問",
        page_icon="🤖",
        layout="wide",
    )
    render_chapter_9_ai()
