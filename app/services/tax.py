"""Ch.6 節稅護城河服務 — 裝潢抵稅白名單分流。

涵蓋：
    - 國稅局裝潢抵稅白 / 黑名單分流

重購退稅章節因純為知識展示（無計算邏輯），不抽至 service；
若未來加入『新舊房價 + 兩年期限』試算，會在此模組擴充。

純函式設計：
    - 嚴禁 `import streamlit`
    - 無外部 I/O，可獨立 unit test
"""

from __future__ import annotations

from typing import NamedTuple


# ============================================================
# 裝潢項目分類常數（暫存於本服務，未來多處引用可上移 SSOT）
# ============================================================
RENOVATION_OPTIONS: tuple[str, ...] = (
    "泥作工程",
    "防水管線",
    "系統家具櫥櫃",
    "高級進口沙發",
    "固定木作衣櫃",
    "窗簾與家電",
)

# 國稅局禁區：可拆卸搬走的『動產』，一律不認列為房屋本體裝修。
# 使用 frozenset 確保不可變、O(1) lookup。
FORBIDDEN_RENOVATION_ITEMS: frozenset[str] = frozenset({
    "系統家具櫥櫃",
    "高級進口沙發",
    "窗簾與家電",
})


# ============================================================
# 服務層內部 DTO
# ============================================================
class RenovationVerdict(NamedTuple):
    """裝潢申報項目分流結果。

    allowed_items:   可列入抵稅的固定不可拆裝修
    forbidden_items: 國稅局禁區（動產，會被剔除甚至罰款）
    has_forbidden:   任一禁區項目命中即 True，UI 應顯示 st.error
    """

    allowed_items: tuple[str, ...]
    forbidden_items: tuple[str, ...]
    has_forbidden: bool


def classify_renovation_items(selected: tuple[str, ...]) -> RenovationVerdict:
    """將申報的裝潢項目分流為『允許抵稅』與『國稅局禁區』兩組。

    對未在 ``RENOVATION_OPTIONS`` 中的未知字串採『寬鬆策略』——
    未在 ``FORBIDDEN_RENOVATION_ITEMS`` 集合者一律歸入 allowed。
    這讓 UI 端新增項目時不會立刻打破服務；若要嚴格驗證，
    呼叫端應另行檢查 ``set(selected) <= set(RENOVATION_OPTIONS)``。

    Args:
        selected: 使用者勾選的項目名稱 tuple。

    Returns:
        RenovationVerdict：分流結果 + 禁區命中旗標。
    """
    allowed = tuple(item for item in selected if item not in FORBIDDEN_RENOVATION_ITEMS)
    forbidden = tuple(item for item in selected if item in FORBIDDEN_RENOVATION_ITEMS)
    return RenovationVerdict(
        allowed_items=allowed,
        forbidden_items=forbidden,
        has_forbidden=len(forbidden) > 0,
    )
