---
name: Finance VC Analyst
description: Venture Capital due diligence, analyzing SaaS metrics, startup traction, and founder profiles.
version: 1.0.0
---

# Finance VC Analyst Workflow

This workflow guides you through the process of evaluating early-stage or growth-stage private companies (startups) for venture capital investment.

## Phase 1: Sourcing & Startup Profile
1. **Y Combinator Database**: Use \`yc-reader\` to fetch profiles, batch information, and descriptions of startups from the YC directory.
2. **Founder & Team Background**: Use \`linkedin-reader\` to analyze the professional history, education, and domain expertise of the founding team.
3. **Public Perception**: Use \`twitter-reader\` to gauge the startup's mindshare, product launches, and community engagement.

## Phase 2: Business Model & Market Analysis
1. **Startup Analysis Framework**: Use \`startup-analysis\` to evaluate the problem, solution, market size (TAM/SAM/SOM), and competitive moat.
2. **Market Trends**: Use \`market-trend-analyst\` to understand macroeconomic tailwinds or headwinds affecting the startup's specific sector.

## Phase 3: SaaS Metrics & Valuation (If applicable)
1. **SaaS Compression**: If the target is a SaaS company, use \`saas-valuation-compression\` to model ARR multiples, Net Revenue Retention (NRR), CAC payback periods, and evaluate how the current macro environment impacts their valuation.
2. **Cap Table & Dilution Modeling**: Project the impact of the current funding round on the capitalization table and founder dilution.

## Phase 4: Investment Memo Generation
1. **Synthesize Due Diligence**: Combine team analysis, market size, product differentiation, and financial metrics.
2. **Draft the Memo**: Produce a structured VC Investment Memo. It should include:
   - Executive Summary
   - Team & Founders
   - Product & Market
   - Traction & Metrics
   - Deal Dynamics & Valuation
   - Key Risks & Mitigations

## Execution Rules:
- Private company data is often sparse; clearly state when estimates or assumptions are being used.
- Focus heavily on team quality and market timing, as these are the biggest drivers of early-stage success.
