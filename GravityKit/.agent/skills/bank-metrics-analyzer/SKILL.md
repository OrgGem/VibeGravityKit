---
name: bank-metrics-analyzer
description: >
  Extract, compute, and analyze specialized financial metrics for Commercial Banks 
  and Financial Institutions. Covers Asset Quality (NPL, NCO), Profitability (NIM, 
  Efficiency Ratio), Capital Adequacy (CET1), and Liquidity (LDR, LCR). Use this 
  skill when analyzing banks (e.g., JPM, BAC, GS, regional banks) because standard 
  corporate metrics (EBITDA, Gross Margin) are invalid.
---

# Bank Metrics Analyzer

Standard financial data aggregators (like Yahoo Finance) often misclassify or omit critical banking metrics. This skill provides the framework to manually extract, calculate, and analyze the true health of a banking institution from its SEC 10-K/10-Q filings or investor presentations.

**Rule of Thumb:** NEVER use EBITDA, Gross Margin, or standard Free Cash Flow for a bank.

## Step 1: Data Extraction Strategy
Since standard APIs fail, you must use `document-reader` or web searches to pull data directly from the bank's **10-K, 10-Q, or Quarterly Earnings Supplements**. Look for the following precise terms in the text:

### 1. Interest & Yield Data
- **Interest Income:** Revenue generated from loans, mortgages, and securities.
- **Interest Expense:** Cost of funding (deposits, borrowed funds).
- **Net Interest Income (NII):** Interest Income - Interest Expense.
- **Average Earning Assets:** The average balance of interest-generating assets.

### 2. Credit Quality (Asset Quality)
- **Non-Performing Loans (NPL) or Non-Performing Assets (NPA):** Loans 90+ days past due.
- **Net Charge-Offs (NCO):** Debt owed to the bank that is unlikely to be recovered.
- **Provision for Credit Losses (PCL):** Expense set aside for future bad loans.
- **Allowance for Credit Losses (ACL):** The balance sheet reserve for bad loans.

### 3. Non-Interest Items
- **Non-Interest Income:** Trading fees, investment banking fees, wealth management fees.
- **Non-Interest Expense:** Salaries, tech infrastructure, real estate.

### 4. Capital & Liquidity
- **Common Equity Tier 1 (CET1) Capital:** Core equity capital compared to risk-weighted assets.
- **Total Deposits** and **Total Loans**.
- **Tangible Common Equity (TCE):** Shareholders' equity minus goodwill and intangible assets.

---

## Step 2: Key Metric Calculations

Calculate the following ratios to assess the bank's fundamental health.

| Category | Metric | Formula | Target / Benchmark |
|---|---|---|---|
| **Profitability** | **Net Interest Margin (NIM)** | `Net Interest Income / Average Earning Assets` | ~2.5% - 3.5% (Varies by rate environment) |
| **Profitability** | **Efficiency Ratio** | `Non-Interest Expense / (Net Interest Income + Non-Interest Income)` | Lower is better. < 60% is excellent. |
| **Profitability** | **ROTCE** | `Net Income / Average Tangible Common Equity` | > 15% is considered strong. |
| **Asset Quality** | **NPL Ratio** | `Non-Performing Loans / Total Loans` | Lower is better. < 1.0% is healthy. |
| **Asset Quality** | **NCO Ratio** | `Net Charge-Offs / Average Total Loans` | < 0.50% in normal cycles. |
| **Capital** | **CET1 Ratio** | `CET1 Capital / Risk-Weighted Assets` | Regulatory minimum usually ~4.5%, but banks target 10%+ |
| **Liquidity** | **Loan-to-Deposit (LDR)** | `Total Loans / Total Deposits` | 70% - 90%. >100% means reliant on wholesale funding. |

---

## Step 3: Analysis Framework (CAMELS Proxy)
When analyzing a bank, synthesize your findings into these categories:

1. **Capital Adequacy:** Is the CET1 ratio comfortably above regulatory requirements? Does the bank have enough buffer to absorb a severe recession?
2. **Asset Quality:** Are NPLs and NCOs rising? Is the Provision for Credit Losses (PCL) increasing relative to previous quarters (signaling economic pessimism)?
3. **Management / Efficiency:** Is the Efficiency Ratio dropping (good) or rising (bad) due to tech investments or inflation in wages?
4. **Earnings:** Is NIM expanding due to higher interest rates, or shrinking due to rising deposit costs (beta)?
5. **Liquidity:** Did the bank suffer deposit flight? Is the Loan-to-Deposit ratio dangerously high?

---

## Step 4: Output Structure
When presenting a bank analysis, use this structure:

1. **Executive Summary:** Overall health and key thesis (e.g., "Strong capital buffer but NIM is compressing due to deposit cost pressures").
2. **Profitability Profile:** NIM trend, Efficiency Ratio, and ROTCE.
3. **Credit Risk & Asset Quality:** NPL trend, NCO ratio, and commentary on Loan Loss Provisions.
4. **Capital & Liquidity Fortress:** CET1 ratio, LDR, and deposit stability.
5. **Key Risks:** E.g., Commercial Real Estate (CRE) exposure, rate cuts, regulatory changes.
