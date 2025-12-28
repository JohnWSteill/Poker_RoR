# Bankroll Expense Accounting — Example

## Strategy & Procedures

This document captures a **practical, repeatable approach** for bankroll expense accounting based on how the data actually appears in the app screenshots.

### Guiding Principles
1. **Only count finalized transactions**  
   - Include amounts shown in **white** (posted transactions).
   - Ignore lighter gray or smaller-font numbers (subtotals, running balances, pending, or contextual UI elements).

2. **Exclude internal transfers**  
   - Transfers between personal accounts or household budgets (e.g. reimbursements, allowance transfers) should **not** be treated as expenses.
   - These are balance movements, not bankroll consumption.

3. **Merchant-level granularity is sufficient**  
   - Do not over-categorize during capture.
   - Date, merchant, and amount are enough; categorization can happen later.

4. **Month attribution follows intent, not posting quirks**
   - If an expense clearly belongs to a poker trip or bankroll activity, include it even if it posts slightly outside the calendar month (note this explicitly when it happens).

5. **Reconstruct first, optimize later**
   - First goal: correct totals.
   - Second goal: clean tables.
   - Automation and tagging come *after* trust in the numbers.

---

## What Was Excluded in This Example
- **+$874.00 transfer** — repayment to household budget (explicitly excluded).
- Any gray / faded / header totals shown in the UI.
- Any inferred balances not explicitly listed as transactions.

---

## Expense Table (Example)

| Date       | Description         | Amount ($) |
|------------|---------------------|------------|
| 2025-07-07 | FREEBETRAN…         | 12.00 |
| 2025-07-19 | Expedia             | 122.37 |
| 2025-07-21 | Pilot Flying J      | 28.90 |
| 2025-07-22 | Kwik Trip           | 24.52 |
| 2025-07-22 | CRUSH LIVE          | 34.99 |
| 2025-07-22 | Tropical Smoothie   | 8.85 |
| 2025-07-27 | Debitcard Hunt…     | 200.00 |
| 2025-07-30 | Kwik Trip           | 29.17 |
| 2025-08-03 | Frontier Airlines   | 26.74 |
| 2025-08-06 | Hy-Vee              | 20.97 |

---

## Totals

- **July 2025 total:** $460.80  
- **All included transactions (example):** **$508.51**

---

## Notes for Future Use
- This file can serve as a **canonical example** when cleaning historical data.
- When ambiguity exists, add a short comment rather than guessing.
- Consistency > perfection.
