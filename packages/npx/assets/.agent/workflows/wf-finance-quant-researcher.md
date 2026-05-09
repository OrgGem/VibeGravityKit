---
name: Finance Quant Researcher
description: Advanced quantitative modeling, correlation analysis, options payoff strategies, and signal tracking.
version: 1.0.0
---

# Finance Quant Researcher Workflow

This workflow guides you through quantitative analysis, statistical correlation, and predictive modeling for trading strategies.

## Phase 1: Data Structuring & Correlation
1. **Define Universe**: Identify the basket of stocks, ETFs, or assets to analyze.
2. **Retrieve Time-Series Data**: Use \`yfinance-data\` to pull high-fidelity historical price and volume data.
3. **Correlation Matrix**: Use \`stock-correlation\` to calculate Pearson/Spearman correlations, identifying highly correlated pairs (for pairs trading) or uncorrelated assets (for portfolio diversification).

## Phase 2: Predictive Modeling & Signals
1. **Run DeepEar/Kronos Models**: Use \`alphaear-deepear-lite\` or \`alphaear-predictor\` to run time-series forecasting or anomaly detection on the dataset.
2. **Signal Tracking**: Use \`alphaear-signal-tracker\` to identify momentum shifts, mean-reversion triggers, or volatility spikes.
3. **Logic Visualization**: Use \`alphaear-logic-visualizer\` to plot the generated signals against historical price action to visually verify the strategy's entry/exit logic.

## Phase 3: Derivatives & Strategy Structuring
1. **Options Analysis**: If the strategy involves options, use \`options-payoff\` to model multi-leg option strategies (straddles, iron condors, verticals) and visualize the risk/reward profile at expiration.
2. **ETF Premium/Discount**: Use \`etf-premium\` if analyzing arbitrage opportunities between an ETF's market price and its Net Asset Value (NAV).

## Phase 4: Validation & Output
1. **Backtest Summary**: Summarize the statistical edge, win rate, and drawdown of the proposed signals (if backtest data is available).
2. **Export Code/Logic**: Write robust Python scripts (using \`python-pro\` skills) to allow the user to run this quantitative model locally in their own environment.

## Execution Rules:
- Always handle missing data (NaNs) appropriately before running correlation matrices.
- Clearly state the assumptions of any predictive model.
- Provide Python code snippets so the user can verify the math and extend the analysis.
