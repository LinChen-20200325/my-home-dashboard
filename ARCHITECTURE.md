# 房產攻略 — 分層架構藍圖（Layered Architecture Blueprint）

> 本文件為「重構藍圖」階段產出，**Phase 1 only**。任何實際搬遷需經明確同意。

---

## 1. 現況問題（Why refactor）

```
my-house-2026/
├── main.py                       # 路由 + sidebar
├── chapter_1.py … chapter_11.py  # UI + 公式 + 常數 + (Ch.9 還含 OpenAI 呼叫)
├── strategy_macro.py             # 同上
├── strategy_negotiation.py       # 同上
├── strategy_syndication.py       # 同上
├── app.py                        # 1,918 行 legacy：PMT / 攤還 / 試算（尚未掛載）
└── requirements.txt
```

每個 `chapter_*.py` 都同時做了：
1. **UI 渲染**（`st.title`, `st.metric`, `st.checkbox` …）
2. **商業邏輯**（DTI 計算、租金係數、判定門檻）
3. **常數定義**（學長硬性門檻散落 14 個檔案）
4. **資料存取**（`chapter_9.py` 直接 import openai SDK + 讀 secrets）

> **痛點**：改 UI 必須讀公式、改公式必須讀 UI；公式重複定義（同一個 DTI 紅線 0.70 寫了兩三次）；OpenAI 呼叫無法被測試；無法接 unit test。

---

## 2. 目標分層結構

```
my-house-2026/
├── app/
│   ├── ui/                          ← Presentation Layer
│   │   ├── pages/                   ← 一個 .py 對應一個側邊欄頁面
│   │   │   ├── chapter_1_cashflow.py
│   │   │   ├── chapter_2_presale.py
│   │   │   ├── chapter_3_rental.py
│   │   │   ├── chapter_4_refinance.py
│   │   │   ├── chapter_5_resale.py
│   │   │   ├── chapter_6_tax.py
│   │   │   ├── chapter_7_exit.py
│   │   │   ├── chapter_8_advanced.py
│   │   │   ├── chapter_9_ai.py
│   │   │   ├── chapter_10_decision.py
│   │   │   ├── chapter_11_combat.py
│   │   │   ├── strategy_macro.py
│   │   │   ├── strategy_negotiation.py
│   │   │   └── strategy_syndication.py
│   │   ├── components/              ← 共用 Streamlit widget
│   │   │   ├── verdict.py           ← 一刀斃命/警告/綠燈 block
│   │   │   └── metric_grid.py
│   │   └── router.py                ← CHAPTERS dict + sidebar
│   │
│   ├── services/                    ← Business Logic Layer（純 Python，禁 streamlit）
│   │   ├── cashflow.py              ← DTI / 淨現金流 / 中產毒藥
│   │   ├── pricing.py               ← 滿租定價 / 議價底價
│   │   ├── mortgage.py              ← PMT / 攤還 / 超額增貸（從 legacy app.py）
│   │   ├── tenant_radar.py          ← 七道信用防線評分
│   │   ├── liquidity.py             ← 老屋脫手紅線 / 自用 5 年鐵證
│   │   ├── tax.py                   ← 裝潢白名單 / 重購退稅
│   │   ├── leverage.py              ← M2 燃料 / 增貸 / 股票質押 / 合資套利
│   │   ├── decision_engine.py       ← Ch.10 四象限判定
│   │   ├── presale_filter.py        ← 建商體質 / 梯戶比 / 合約地雷
│   │   └── ai_advisor.py            ← 對話編排（system prompt + history）
│   │
│   ├── repositories/                ← Data Access Layer（外部 I/O）
│   │   ├── openai_client.py         ← OpenAI SDK 包裝 + streaming
│   │   └── secrets.py               ← st.secrets / sidebar 雙來源
│   │
│   ├── models/                      ← Domain Models（dataclass DTO）
│   │   ├── property.py              ← PropertySpec, PriceInfo
│   │   ├── tenant.py                ← CreditDefenseScore
│   │   ├── cashflow.py              ← CashflowSnapshot, DTIVerdict
│   │   ├── ai.py                    ← ChatMessage, ChatTurn
│   │   └── constants.py             ← 學長硬性門檻 SSOT
│   │
│   └── main.py                      ← Composition root（set_page_config + router）
│
├── tests/                           ← （可選）pytest 單元測試
│   ├── services/
│   └── models/
│
├── app.py                           ← 🚧 LEGACY（待退役）
├── requirements.txt
├── ARCHITECTURE.md
└── STATE.md
```

---

## 3. 各層嚴格職責（Strict Responsibilities）

### 3.1 UI Layer (`app/ui/`)
| 允許 | 嚴禁 |
|---|---|
| ✅ Streamlit 元件（title/metric/checkbox/error） | ❌ 寫公式（DTI、套利、增貸） |
| ✅ 收集使用者輸入 → 包成 DTO | ❌ 直接呼叫 OpenAI |
| ✅ 接收 Service 回傳 DTO → 渲染 | ❌ 直接讀 secrets |
| ✅ 版型編排（columns / tabs / expander） | ❌ 跨頁 import 別頁 widget |

### 3.2 Service Layer (`app/services/`)
| 允許 | 嚴禁 |
|---|---|
| ✅ 純 Python 函式 / pure functions | ❌ `import streamlit` |
| ✅ 輸入 DTO → 輸出 DTO | ❌ 印任何 UI 元素 |
| ✅ 商業判定（學長心法、公式） | ❌ 直接呼叫 OpenAI SDK |
| ✅ 呼叫 repositories 取資料 | ❌ 跨 service 反向依賴 |

### 3.3 Repository Layer (`app/repositories/`)
| 允許 | 嚴禁 |
|---|---|
| ✅ 包裝外部 SDK（openai、未來 DB） | ❌ 寫商業邏輯（如要重試幾次） |
| ✅ Raw response → model DTO 轉換 | ❌ 印任何 UI 元素 |
| ✅ 處理連線錯誤、retry、timeout | ❌ 知道誰要呼叫它 |

### 3.4 Models Layer (`app/models/`)
| 允許 | 嚴禁 |
|---|---|
| ✅ `@dataclass(frozen=True)` 定義型別 | ❌ import 其他層 |
| ✅ 模組常數（門檻 SSOT） | ❌ 任何 I/O |
| ✅ Enum / typed alias | ❌ 商業邏輯 |

### 3.5 依賴方向（單向，不可逆）

```
   UI ────► Service ────► Repository
    │         │              │
    └────► Models ◄──────────┘
```

- UI **永遠不可直接** import repositories
- Models 不依賴任何層
- 違反方向 → import 時會 circular，CI 應該 fail

---

## 4. 搬遷地圖（Module Migration Map）

| 現有檔案 | UI 落點 | Service 拆分 | Repository / Model |
|---|---|---|---|
| `main.py` | `app/main.py` + `app/ui/router.py` | — | — |
| `chapter_1.py` | `ui/pages/chapter_1_cashflow.py` | `services/cashflow.py` + `services/leverage.py` (M2) | `models/cashflow.py` |
| `chapter_2.py` | `ui/pages/chapter_2_presale.py` | `services/presale_filter.py` | `models/property.py` |
| `chapter_3.py` | `ui/pages/chapter_3_rental.py` | `services/pricing.py` + `services/tenant_radar.py` | `models/tenant.py` |
| `chapter_4.py` | `ui/pages/chapter_4_refinance.py` | `services/leverage.py` (增貸 + 科目四) | `models/property.py` |
| `chapter_5.py` | `ui/pages/chapter_5_resale.py` | `services/liquidity.py` (地雷 + SOP) | — |
| `chapter_6.py` | `ui/pages/chapter_6_tax.py` | `services/tax.py` + `services/leverage.py` (股票質押) | — |
| `chapter_7.py` | `ui/pages/chapter_7_exit.py` | `services/liquidity.py` (脫手紅線 + 鐵證) | — |
| `chapter_8.py` | `ui/pages/chapter_8_advanced.py` | `services/presale_filter.py` + `services/leverage.py` (空租準備金) | — |
| `chapter_9.py` | `ui/pages/chapter_9_ai.py` | `services/ai_advisor.py` | `repositories/openai_client.py` + `repositories/secrets.py` + `models/ai.py` |
| `chapter_10.py` | `ui/pages/chapter_10_decision.py` | `services/decision_engine.py` | — |
| `chapter_11.py` | `ui/pages/chapter_11_combat.py` | UI-only（無公式） | — |
| `strategy_macro.py` | `ui/pages/strategy_macro.py` | `services/leverage.py` (M2/M1B 黃金交叉) | — |
| `strategy_negotiation.py` | `ui/pages/strategy_negotiation.py` | `services/pricing.py` (議價戰術) | — |
| `strategy_syndication.py` | `ui/pages/strategy_syndication.py` | `services/leverage.py` (合資套利 + 防護鎖) | — |
| `app.py` (legacy) | （捨棄或保留為 `ui/pages/legacy_full.py`） | `services/mortgage.py` (PMT / 攤還) | — |

---

## 5. 為什麼這樣切？

1. **Token 控管** — 改 UI 時不必再讀公式檔；改公式時不必再讀 UI 樣板。Claude/Codex 只讀「相關層」即可。
2. **可測性** — services 是 pure functions，pytest 不啟動 Streamlit、不打 OpenAI 也能跑。
3. **AI 安全性** — OpenAI 呼叫集中在 `repositories/openai_client.py`，未來要加 rate limit / token budget / retry / spend cap 改一處即可。
4. **未來擴展** — 若從 Streamlit 改 FastAPI + React，UI 層整層丟掉，services / repositories 完全不動。
5. **SSOT (Single Source of Truth)** — `models/constants.py` 統一硬性門檻（`DTI_DANGER = 0.70`, `MIN_SAFE_PING = 15`, `EXIT_AGE_RED_LINE = 35`, `ELEVATOR_RATIO_DANGER = 4.0`），杜絕硬編碼漂移。

---

## 6. 接下來步驟

藍圖已備齊；逐步搬遷的 33 個 Todo 已寫入 [STATE.md](./STATE.md)。

**等待使用者明確同意（覆「同意」）後**，方可進入 Phase 2「逐層解耦與搬遷」。Phase 2 一次只動一個檔案，並執行『自我審核五步驟』（邏輯審查 → 邊界測試 → 效能評估 → Debug 修正 → 最終代碼）。
