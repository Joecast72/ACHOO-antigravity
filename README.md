# ACHOO Antigravity

**ACHOO Antigravity** is a pharmacist-built AI medication safety project designed to identify hypoglycemia risk in older adults with diabetes and generate explainable pharmacist follow-up recommendations.

ACHOO stands for:

**Adherence and Compliance Health Outcome Organization**

This project focuses on a high-risk geriatric diabetes scenario where medication burden, kidney function, prior hypoglycemia, low A1c, falls, dizziness, and poor appetite can combine into a preventable medication safety problem.

---

## Clinical Problem

Older adults with diabetes are at increased risk for medication-related harm, especially when treated with insulin, sulfonylureas, or complex multi-drug regimens.

Hypoglycemia in older adults can lead to:

- Falls
- Emergency department visits
- Hospitalization
- Functional decline
- Loss of independence
- Avoidable medication harm

Many clinical systems store the necessary risk signals, but they are often scattered across medication lists, labs, history, and clinical notes.

ACHOO demonstrates how an AI-assisted pharmacist safety agent can identify those signals, explain the risk, and recommend a practical follow-up plan.

---

## What This Project Does

ACHOO evaluates a patient profile and identifies hypoglycemia risk factors such as:

- Prior severe hypoglycemia or ED visit
- Insulin therapy
- Sulfonylurea therapy
- Low A1c / possible overtreatment
- Chronic kidney disease
- Recent fall or dizziness
- Poor appetite or inconsistent intake
- Polypharmacy and geriatric vulnerability

The system produces:

- A structured risk score
- Triggered clinical factors
- Evidence-based explanations
- Pharmacist-facing recommendations
- A follow-up flag written back to MongoDB

---

## Demo Patient

The initial demo case uses an older adult patient with type 2 diabetes and multiple hypoglycemia risk factors.

Example risk signals include:

- Age 78
- Type 2 diabetes
- Chronic kidney disease stage 3
- A1c 6.4%
- Insulin glargine
- Glipizide
- Poor appetite
- Dizziness
- Recent fall
- Prior hypoglycemia emergency department visit

ACHOO identifies this patient as high risk and recommends pharmacist review for possible overtreatment and medication safety intervention.

---

## Live API

The project includes a Flask API deployed on Google Cloud Run and connected to MongoDB Atlas.

Example endpoint:

```text
GET /patient/SYN-001