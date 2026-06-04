\# ACHOO — Adherence and Compliance Health Outcome Organization



ACHOO is a pharmacist-led medication safety triage prototype for older adults with diabetes, chronic kidney disease, fall risk, and polypharmacy.



This project demonstrates a transparent clinical decision-support workflow:



1\. Retrieve a synthetic patient record from MongoDB

2\. Apply the ACHOO clinical scoring engine

3\. Generate module-level medication safety risk results

4\. Produce a pharmacist-facing audit trail

5\. Write the assessment back to MongoDB



\## Current Prototype Status



Working components:



\- ACHOO clinical scoring engine

\- Synthetic Velma Johnson case

\- Flask API endpoints

\- MongoDB read/write workflow

\- MongoDB assessment write-back

\- Pytest validation for the Velma worked example

\- Local verification script for MongoDB read/write flow



\## Important Clinical Boundary



ACHOO is a pharmacist triage and decision-support aid.



It is not:



\- a diagnostic device

\- an autonomous prescriber

\- a validated clinical prediction instrument

\- a replacement for pharmacist or clinician judgment



Every medication-related output requires human pharmacist review before any medication change.



\## Core Workflow



```text

MongoDB patient record

→ Flask API

→ ACHOO score\_patient()

→ structured medication-safety assessment

→ MongoDB write-back

## License

This project is licensed under the MIT License.

