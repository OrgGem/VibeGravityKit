---
name: Finance Market Monitor
description: Real-time sentiment tracking across social media and news to build a daily market briefing dashboard.
version: 1.0.0
---

# Finance Market Monitor Workflow

This workflow is designed to run continuously or on a daily schedule to track market sentiment, systemic risks, and breaking news.

## Phase 1: Real-time Data Ingestion
1. **News & Geopolitics**: Use \`alphaear-news\` and \`hormuz-strait\` to monitor breaking macroeconomic, geopolitical, and specific commodity-related news (e.g., oil supply chain disruptions).
2. **Social Media Streams**: Use \`twitter-reader\` to track trending tickers (cashtags), influencer sentiment, and breaking retail narratives.
3. **Community Chatter**: Use \`telegram-reader\` or \`discord-reader\` to monitor specialized trading communities, crypto alphas, or localized sentiment shifts.

## Phase 2: Sentiment Aggregation
1. **Analyze Polarity**: Use \`finance-sentiment\` or \`alphaear-sentiment\` to process the raw text from Phase 1 into measurable scores (Bullish, Bearish, Neutral).
2. **Identify Anomalies**: Use \`alphaear-signal-tracker\` to flag unusual spikes in chatter volume or sudden shifts in sentiment polarity that diverge from price action.

## Phase 3: Dashboard Design & Reporting
1. **Data Structuring**: Aggregate the sentiment scores, key news headlines, and flagged anomalies into a clean JSON or tabular format.
2. **Dashboard Creation**: Use \`kpi-dashboard-design\` and \`generative-ui\` to design a visual dashboard layout (e.g., a React component or a structured Markdown table) that displays:
   - Top 5 Trending Tickers
   - Overall Market Sentiment Score
   - Key Geopolitical Risks
   - Community Chatter Highlights
3. **Daily Recap**: Use \`earnings-recap\` (if earnings season) and \`data-storytelling\` to write a concise 1-page morning briefing for traders.

## Execution Rules:
- Filter out spam, bot activity, and duplicate news articles during the aggregation phase.
- Highlight actionable insights (e.g., "Ticker XYZ has a 300% spike in positive sentiment with no price movement yet").
- Ensure the final dashboard or briefing is highly scannable (use bullet points, bold text, and clear headers).
