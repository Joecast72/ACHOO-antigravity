# ACHOO Project Instructions

ACHOO stands for Adherence and Compliance Health Outcome Organization.

This project is a pharmacist-led medication safety triage system for older adults.

The agent must:
- Treat ACHOO as clinical decision support, not diagnosis or autonomous prescribing.
- Apply the six ACHOO scoring modules exactly as defined in docs/ACHOO_Clinical_Scoring_Spec_v1.md.
- Never invent missing clinical data.
- Distinguish evidence-anchored modules from expert-defined composite reasoning.
- Always end clinical outputs with: Pharmacist review required before any medication change.
- Never commit secrets, API keys, or MongoDB passwords.
- Prefer small, testable changes.
- Run tests after modifying scoring logic.
