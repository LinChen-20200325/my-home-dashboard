# Legacy code (retained for reference, not maintained)

This directory holds the pre-refactor standalone scripts. None of these
files are imported by the live app — they're kept here so future readers
can see the original design that fed into the layered architecture.

## Contents

### `app.py` (1,918 lines)
The original single-file "買房前自我能力與現金流健檢" Streamlit app.
It was never wired into the multi-chapter `main.py`, so its features
sat unused for the entire feature build. During Phase 2 #11 the PMT
engine and amortization schedule were extracted to
`app/services/mortgage.py`; the rest of this file (full-width sidebar,
detailed cashflow analysis, mortgage stress tester, rent safety index,
income reverse-projector) overlaps with Ch.1 + Ch.4 but with a
different UI layout.

Use it as a reference design or harvest specific charts; do **not**
import from it.

To preview standalone:
```bash
streamlit run _legacy/app.py
```

## Why keep this around?

1. The PMT engine and amortization table moved to
   `app/services/mortgage.py` — but the **UI layout** of the original
   app (multi-tab cashflow / stress / income panels) is not yet
   replicated in the new chapter pages.
2. If a future iteration wants to bring back any of those views,
   adapting from this file is faster than rebuilding from scratch.
3. Git history alone would not reveal the full file shape after
   deletion; keeping it visible at `_legacy/app.py` documents
   intent and provides a reference.

If you decide this is dead weight, `git rm -r _legacy/` is safe —
nothing in the live app imports from here.
