# Agentic Credit-Risk Underwriting

## Business problem
Underwriting decisions are often slow, inconsistent, and hard to defend in regulated audits. Teams need faster decisions with transparent reasoning.

## Agent architecture
A Chief Underwriter agent orchestrates specialist agents for:
- Applicant and income analysis
- Fraud and identity risk checks
- Collateral and affordability assessment
- Policy and compliance validation
- Final decision synthesis with rationale

## Stack
- Python, FastAPI
- AWS Bedrock, LangGraph-style multi-agent orchestration
- XGBoost + SHAP for interpretable risk scoring
- PostgreSQL, Docker

## Result
Delivers regulator-ready, explainable underwriting decisions with clear audit trails and reusable decision artifacts for risk and compliance teams.
