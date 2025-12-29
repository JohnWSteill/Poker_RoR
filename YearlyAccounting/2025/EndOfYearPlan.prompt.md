# End-of-Year Bankroll Reconciliation Prompt

**For:** December 2026  
**Created:** December 29, 2025

---

## Hey Future John (and Copilot),

It's EOY reconciliation time again. Last year was a mess — don't let it get that bad. Here's what you need to do:

---

## The Four Things

1. **Track down all expenses**
2. **Count up all assets**  
3. **Compare against W/L ledger and calculate leakage**
4. **Update investor apportionments**

---

## Key Numbers You'll Need

### Starting Point (1/1/26)
| Investor | Equity | % |
|----------|--------|---|
| John | $35,378.68 | 50.54% |
| Jeff | $34,621.32 | 49.46% |
| **Total BR** | **$70,000.00** | 100% |

*Note: Actual assets were $73,233.29 but ~$3,233 was reserved for BTC tax liability*

### Profit Split Structure
- **Player share:** 50% of net profit → John
- **Investor share:** 50% of net profit → split by investor %

### Jeff's Equity Formula (PROTECT THIS)
```
Jeff EOY = Jeff BOY + (Net Profit × 50% × Jeff%)
         - Any distributions to Jeff
```

---

## Data Sources to Gather

1. **Monarch** — Export all "Poker Expenses" category for the year
2. **Bank 1102** — Check for Hungry Horse, Crush Live, other poker subs
3. **Session logs** — Should be in Results_2026.csv or similar
4. **PAYCHECKS.csv** — Track all paychecks taken
5. **Coinbase** — BTC holdings and USD balance

---

## Common Gotchas from 2025

- [ ] **Transfers are NOT expenses** — filter out positive amounts in Monarch
- [ ] **Pay is NOT an expense** — investors bear expenses, pay comes from player share
- [ ] **Track investor equity by addition, not multiplication** — Jeff's equity = start + profit share, NOT (EOY BR × %)
- [ ] **BTC tax liability** — if you sold BTC, accrue the tax as expense even if not paid yet
- [ ] **The "John's Debt" $10k** — keep it in BR for RoR calcs, it's psychological + available if needed

---

## Monthly Habits (Did You Keep Up?)

Check `monthly_accounting_checklist.md` — if you did this monthly, EOY is easy. If not... well, you know the drill.

---

## Files in This Archive

| File | Purpose |
|------|---------|
| `EndOfYear_25_BR_reconcilliation_plan.prompt.md` | The full 2025 reconciliation workthrough |
| `2025_final_summary.md` | Clean final numbers |
| `poker_expenses_in_monarch_2025.csv` | Monarch expense export |
| `PAYCHECKS_2025.csv` | Paycheck records |

---

## The Fun Part

Once reconciliation is done, update your RoR model and figure out stakes for 2027 trips!

Good luck. Don't procrastinate.

— Past John
