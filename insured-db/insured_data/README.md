# AI Agent Insure — Insureds Dataset

This folder contains 5 linked CSV files representing a fictional internal insurance database for 100 insureds.

## Files Included

### 1. insureds.csv

Contains PII and demographic/company info.
Linked by: **Insured_ID**

### 2. policies.csv

List of all policies for each insured.
Linked by: **Insured_ID**, **Policy_Number**

### 3. coverage_details.csv

Coverage limits, deductibles, and optional add-ons.
Linked by: **Policy_Number**

### 4. ai_risk_profile.csv

AI system footprint and underwriting risk factors.
Linked by: **Policy_Number**

### 5. claims_history.csv

Historical AI incident claims.
Linked by: **Insured_ID**, **Policy_Number**

## Notes

- All data is fictional.
- Designed for internal use, RAG ingestion, or analytics pipelines.

## 📜 License

© 2025 AI Agent Insure. Reimagining Insurance for the Agentic AI Era.
