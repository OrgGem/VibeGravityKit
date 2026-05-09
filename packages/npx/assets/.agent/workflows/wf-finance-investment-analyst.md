---
name: Finance Investment Analyst
description: End-to-end fundamental and technical analysis for a specific ticker, generating a comprehensive investment report.
version: 1.0.0
---

# Finance Investment Analyst Workflow

This workflow guides you through analyzing a publicly traded company using a combination of fundamental data, technical indicators, and alternative news sentiment.

## Phase 1: Data Gathering (Fundamental & Technical)
1. **Retrieve Price Action**: Use \`yfinance-data\` to fetch historical price data, volume, and moving averages for the target ticker.
2. **Collect Financial Statements**: Use \`funda-data\` and \`yfinance-data\` to pull the Income Statement, Balance Sheet, and Cash Flow metrics.
3. **Capture Earnings & Estimates**: Use \`earnings-preview\` and \`estimate-analysis\` to understand consensus expectations and upcoming events.

## Phase 2: Valuation and Strategy Evaluation
1. **Intrinsic Valuation**: Use \`company-valuation\` to perform a DCF (Discounted Cash Flow) or Comparable Company Analysis based on the gathered data.
2. **Technical Setup Assessment**: Use \`sepa-strategy\` to evaluate if the stock meets the criteria for a Specific Entry Point Analysis (trend template, consolidation, volatility contraction).
3. **Check Institutional Liquidity**: Use \`stock-liquidity\` to understand if the stock has sufficient liquidity for institutional entry/exit without massive slippage.

## Phase 3: Alternative Data & Sentiment
1. **News & Market Context**: Use \`alphaear-news\` to fetch the latest news articles and press releases related to the company.
2. **Sentiment Analysis**: Use \`finance-sentiment\` or \`alphaear-sentiment\` to gauge whether the narrative is bullish, bearish, or mixed based on recent publications.

## Phase 4: Report Generation & Presentation
1. **Synthesize Findings**: Combine the valuation, technical setup, and sentiment into an investment thesis (Buy/Hold/Sell). Use \`data-storytelling\` to structure the narrative.
2. **Generate Report**: Use \`alphaear-reporter\` to format the research into a standardized report structure.
3. **Create Presentation (Optional)**: If requested by the user, use \`gen-doc-ppt-master\` to generate a PowerPoint presentation summarizing the investment thesis.

## Execution Rules:
- Always cross-reference fundamental data (e.g., P/E ratio) with historical averages.
- If data is missing from one source, attempt to infer or calculate it using secondary sources.
- The final report MUST include a clear thesis, key catalysts, and identified risks.
