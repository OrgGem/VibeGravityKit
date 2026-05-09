---
name: bank-valuation-ddm
description: >
  Valuation models exclusively for Banks and Financial Institutions. Implements 
  the Dividend Discount Model (DDM), Residual Income Model (RIM), and Price to 
  Tangible Book Value (P/TBV) regression. Use this skill instead of standard DCF 
  when valuing banks.
---

# Bank Valuation Models

Banks cannot be valued using a traditional Discounted Cash Flow (DCF) model because their cash flows are obscured by their operations (loans are assets, deposits are liabilities). Furthermore, CapEx and Working Capital changes are fundamentally different for financial institutions.

This skill provides three accepted methods for valuing a bank:
1. **Dividend Discount Model (DDM)** (Primary intrinsic method)
2. **Residual Income Model (RIM)** (Alternative intrinsic method)
3. **Relative Valuation (P/B, P/TBV, P/E)**

---

## Method 1: Dividend Discount Model (DDM)

The DDM assumes the value of a bank is the present value of all its future dividend payments. Since banks are heavily regulated, their capital returns (dividends + buybacks) are closely tied to their earnings and capital requirements.

### Formula
`Value = Sum of PV of Expected Dividends (Years 1 to N) + PV of Terminal Value`

### Steps to Compute:
1. **Estimate Cost of Equity (Ke):** Use CAPM (`Ke = Risk Free Rate + Beta * Equity Risk Premium`). *Note: Banks do not use WACC, they only use Cost of Equity.*
2. **Forecast Earnings (Net Income):** Forecast Net Income for the next 5 years based on asset growth and NIM assumptions.
3. **Determine Payout Ratio:** Calculate the historical payout ratio (`Dividends Paid / Net Income`). Adjust if the bank is signaling higher/lower buybacks.
4. **Calculate Expected Dividends:** `Forecasted Net Income * Payout Ratio`.
5. **Terminal Value (Gordon Growth):** `TV = Expected Dividend(Year 5 * (1 + g)) / (Ke - g)`. where `g` is long-term growth rate (~2-3%).
6. **Discount to Present Value:** Discount all forecasted dividends and the Terminal Value back to Year 0 using `Ke`.

---

## Method 2: Residual Income Model (RIM)

Also known as the Excess Return Model. It values a bank based on its current Book Value plus the present value of its future "excess" returns (returns above its Cost of Equity).

### Formula
`Value = Current Book Value of Equity + Sum of PV of Residual Income`
Where:
`Residual Income = (ROE - Cost of Equity) * Beginning Book Value`

### Why it works for banks:
Banks are inherently tied to their Book Value (capital). If a bank generates an ROE of 12% and its Cost of Equity is 10%, it creates positive residual income, meaning it should trade at a premium to its Book Value (P/B > 1). If ROE < Ke, it destroys value and should trade at a discount (P/B < 1).

---

## Method 3: Relative Valuation (P/TBV vs ROTCE)

The most robust way to perform relative valuation for banks is to plot **Price to Tangible Book Value (P/TBV)** against **Return on Tangible Common Equity (ROTCE)**.

1. **Gather Peer Data:** Find 5-10 peer banks.
2. **Extract Metrics:** For each peer, get their `P/TBV` ratio and their `ROTCE`.
3. **Regression / Correlation:** There is a strong linear relationship between ROTCE and P/TBV. A bank generating 15% ROTCE will command a higher P/TBV multiple than a bank generating 8% ROTCE.
4. **Target Valuation:** Find where the target bank sits on the regression line. If its fundamental ROTCE is 12%, the regression line implies a fair P/TBV of, say, 1.4x.
5. **Implied Share Price:** `Implied Price = Implied P/TBV Multiple * Target's Tangible Book Value per Share`.

---

## Execution Guide for Agents

When a user asks to "value JPM" or "what is the fair value of Bank of America":

1. **Reject DCF:** Explicitly state that DCF is invalid for banks.
2. **Gather Data:** Use `funda-data` or `yfinance-data` to get:
   - Current Share Price, Shares Outstanding
   - Book Value of Equity, Tangible Book Value
   - TTM Net Income, TTM Dividends Paid
   - Beta, Risk-Free Rate
3. **Run DDM:** Build a quick 5-year DDM using historical ROE to project earnings and historical payout ratios to project dividends.
4. **Run Relative:** Compare P/B and P/E against peers.
5. **Triangulate:** Present a blended valuation based on DDM and Relative Valuation.
