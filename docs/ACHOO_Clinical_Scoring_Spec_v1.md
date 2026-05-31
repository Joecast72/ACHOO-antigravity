# ACHOO — Clinical Scoring Specification
### Adherence and Compliance Health Outcome Organization
**Pharmacist-led medication safety triage for older adults**

Version 1.0 — clinical logic specification (build-agnostic)

---

## 0. What this document is

This is the **clinical reasoning engine** behind ACHOO, written so it can be implemented in any agent framework. It defines six evidence-mapped risk modules, a composite layer that reasons across them, the system-prompt logic, the data/audit format, and — most importantly — the honesty boundaries that keep the whole thing credible.

**Read this first, before any implementation:**

ACHOO is a **pharmacist triage and decision-support aid**, not a diagnostic device, not an autonomous prescriber, and not a validated clinical prediction instrument. It surfaces medication-safety concerns for a human pharmacist to review. Every output ends with human-in-the-loop review required before any medication change.

### The credibility distinction that governs everything

There are two kinds of logic in ACHOO, and they must never be blurred:

1. **Borrowed validation** — individual module triggers anchored to published instruments and guidelines (Karter et al. 2017, AGS Beers 2023, STOPP/START v3, STOPPFall, KDIGO 2024, ADA Standards of Care Older Adults, Medication Appropriateness Index). These are defensible because someone else validated them.

2. **Expert-defined reasoning** — the point weights, the composite/compounding layer, the cross-module interaction links, and the overall-tier escalation rule. These are clinically reasonable but are **NOT** drawn from a validated multi-domain instrument (to current knowledge, no validated composite geriatric medication-risk score across these exact domains exists).

Every output, demo, and write-up must lead with this distinction. Claiming the composite layer is "validated" would be overreach and is the fastest way to lose clinical credibility.

### ⚠️ Verification obligation

Every drug classification, threshold, point value, and interaction in this document reflects a best-effort understanding of the cited guidelines **at the time of writing**. Guidelines change (SGLT2 and GLP-1 indications especially are evolving quickly). **A licensed pharmacist must verify all classifications against the current published criteria — Beers 2023, STOPP/START v3, STOPPFall, KDIGO 2024, ADA 2025/2026, and live drug-interaction references — before any clinical or even demonstration use.**

---

## 1. The reference patient — Mrs. Velma Johnson (synthetic)

Used throughout for worked examples. Entirely synthetic; no real patient data.

| Field | Value |
|---|---|
| patient_id | SYN-001 |
| Age | 78 |
| Conditions | Type 2 Diabetes, CKD Stage 3, Fall history |
| Labs | A1c 6.4%, eGFR 42 mL/min/1.73m² |
| Medications | glipizide, insulin glargine, semaglutide, empagliflozin, hydrochlorothiazide, lisinopril |
| Clinical flags | recent fall, dizziness, poor appetite, prior hypoglycemia ED visit |

---

## 2. Global scoring rules

- Each module has its own max score and its own LOW/MODERATE/HIGH tiers.
- **Score only factors clearly supported by the patient data. Never invent missing information.** If a value is absent, state it as "not available — unable to assess" and do not trigger the dependent factor.
- A module's **raw** score may exceed its max; the **displayed/capped** score never exceeds the max.
- **Risk tier is assigned from the raw score** (so a very high raw score still reads HIGH even after capping).
- Modules are scored independently first; cross-module synthesis happens only in the composite layer (Section 9), with explicit anti-double-counting rules.

---

## 3. MODULE 1 — Hypoglycemia Risk (max 25)

**Anchor:** Karter et al. 2017 (validated hypoglycemia-related ED/hospital risk tool) + ADA Standards of Care, Older Adults.
**Framing:** This is ACHOO's most strongly validated module — the weight hierarchy follows the relative risk magnitude reported in the source literature where available.

| Trigger | Points | Source |
|---|---|---|
| Prior severe hypoglycemia or ED/hospital visit for hypoglycemia | 8 | Karter et al. 2017 |
| Insulin therapy (any type) | 7 | Karter et al. 2017; ADA |
| Sulfonylurea or meglitinide use | 6 | ADA Standards, Older Adults |
| CKD Stage 3+ or eGFR <45 | 5 | KDIGO 2024 |
| Age ≥75 | 3 | ADA Older Adults |
| Poor oral intake / missed meals / anorexia | 3 | ADA Older Adults |
| A1c <7.0% while on insulin/sulfonylurea/meglitinide | 2 | ADA; AGS Beers 2023 |

**Tiers (raw):** 0 = none · 1–15 = LOW · 16–24 = MODERATE · 25+ = HIGH

**Velma:** 8+7+6+5+3+3+2 = **34 raw → 25/25 capped → HIGH**

---

## 4. MODULE 2 — Falls & Orthostasis Risk (max 20)

**Anchor:** AGS Beers 2023, STOPP/START v3, STOPPFall.
**Framing — GUIDELINE-FLAGGED, NOT INDEPENDENTLY PREDICTIVE:** These criteria flag drugs/factors associated with fall risk in older adults; they do not provide validated per-patient probabilities. The score surfaces concerns for review. The one exception is *prior fall history*, which is a genuinely well-established independent predictor — hence its top weight.

| Trigger | Points | Source |
|---|---|---|
| Prior fall / recurrent falls documented | 6 | STOPP/START v3; STOPPFall |
| Benzodiazepine, Z-drug, or sedative-hypnotic | 5 | Beers 2023; STOPPFall |
| Antihypertensive/vasodilator **+ documented orthostasis/dizziness** | 4 | STOPP/START v3 |
| Loop/thiazide diuretic **+ dizziness/volume symptoms** | 4 | Beers 2023; STOPP/START v3 |
| Anticholinergic burden (≥2 anticholinergic agents) | 3 | Beers 2023 |
| Antipsychotic or antiepileptic use | 3 | STOPPFall |
| Polypharmacy ≥5 medications | 2 | Beers 2023 |

**Design note:** Two triggers require a **drug + symptom pairing**, mirroring how STOPP actually works (e.g., vasodilators *in patients with postural hypotension*), not a blanket drug penalty.

**Tiers (raw):** 0–5 = LOW · 6–11 = MODERATE · 12–20 = HIGH

**Velma:** prior fall 6 + HCTZ+dizziness 4 + lisinopril+dizziness 4 + polypharmacy 2 = **16 → 16/20 → HIGH**

---

## 5. MODULE 3 — Renal & Dehydration Risk (max 15)

**Anchor:** KDIGO 2024 + FDA labeling.
**Framing — THREE-PART, AVOIDS THE "PROTECTIVE-LOOKS-RISKY" TRAP:** Naive tools penalize any renally-active drug. ACHOO separates (A) volume/dehydration risk, (B) drug-clearance risk that amplifies other modules, and (C) renal appropriateness — explicitly crediting SGLT2 inhibitors and ACE/ARBs as **renally protective** in CKD rather than penalizing them.

### Part A — Volume / Dehydration (max 7)
| Trigger | Points | Source |
|---|---|---|
| Loop or thiazide diuretic | 3 | KDIGO 2024; Beers 2023 |
| Poor fluid intake / dehydration symptoms | 2 | KDIGO 2024 |
| SGLT2 inhibitor — **acute/sick-day context only** | 2 | FDA; KDIGO sick-day guidance |

### Part B — Drug-Clearance Risk (max 5) — *the bridge to other modules*
| Trigger | Points | Source |
|---|---|---|
| eGFR <45 with ≥1 renally-cleared high-risk drug | 3 | KDIGO 2024 |
| NSAID use in CKD | 2 | Beers 2023; FDA |

### Part C — Renal Appropriateness (NO POINTS — routing/credit)
| Finding | Output |
|---|---|
| SGLT2 in CKD, eGFR within indicated range | ✓ APPROPRIATE — renally protective; do NOT deprescribe for renal reasons |
| ACE/ARB in CKD | ✓ APPROPRIATE — renally protective (monitor K⁺, eGFR) |
| Renally-cleared drug not dose-adjusted for eGFR | ⚠ INAPPROPRIATE — dose review |
| NSAID in CKD | ⚠ INAPPROPRIATE — recommend discontinuation |

**Tiers (raw, Parts A+B):** 0–4 = LOW · 5–9 = MODERATE · 10–15 = HIGH

**Velma:** A: HCTZ 3 + poor intake 2 + empagliflozin 0 (chronic, not acute) = 5; B: eGFR42 + renally-cleared drugs 3 = 3 → **8 → 8/15 → MODERATE**. Part C: empagliflozin & lisinopril flagged APPROPRIATE/protective; insulin+glipizide renally-cleared at eGFR42 → dosing review.

---

## 6. MODULE 4 — GLP-1 / Frailty / Nutrition Risk (max 15)

**Anchor:** ADA Standards of Care, Older Adults + geriatric frailty literature.
**Framing — FLAG RISK AND FLAG THE UNKNOWN:** GLP-1 appetite suppression/weight loss is a genuine concern in a frail, poor-intake elder. BUT the right action depends on *why* the drug was prescribed (glucose-lowering vs. cardiovascular/renal protection), which cannot be determined from medication data alone. ACHOO surfaces both the nutrition risk and the indication uncertainty, and routes the decision to the pharmacist. It does not recommend stopping potentially protective therapy on its own.

### Part A — Nutrition / Frailty (max 15)
| Trigger | Points | Source |
|---|---|---|
| GLP-1 RA + documented weight loss >5% / ongoing unintended loss | 5 | ADA Older Adults; frailty consensus |
| GLP-1 RA + poor appetite / reduced intake | 4 | ADA Older Adults |
| Clinical frailty indicators (fall, weakness, slow gait, exhaustion) | 3 | ADA Older Adults |
| GLP-1 RA + GI symptoms (nausea, vomiting, constipation) | 2 | FDA; ADA |
| BMI <22 / low weight / sarcopenia | 1 | Geriatric nutrition consensus |

### Part B — Indication Flag (NO POINTS — routing)
| Finding | Output |
|---|---|
| GLP-1 indication not determinable from data | ⚠ INDICATION UNKNOWN — pharmacist must establish glucose-lowering vs. CV/renal protection |
| Glucose-lowering only + A1c <7.0 in frail elder | ⚠ Possible overtreatment — nutrition harm without glycemic justification |
| CV/renal protective indication | ⚠ Protective benefit may offset nutrition concern — do NOT deprescribe on nutrition grounds alone |

**Tiers (raw, Part A):** 0–4 = LOW · 5–9 = MODERATE · 10–15 = HIGH

**Velma:** semaglutide+poor appetite 4 + frailty indicators 3 = **7 → 7/15 → MODERATE** (weight loss/BMI not documented → not assumed). Part B: INDICATION UNKNOWN; if glucose-lowering only, likely overtreatment at A1c 6.4.

---

## 7. MODULE 5 — Polypharmacy & Medication Appropriateness (max 15)

**Anchor:** Medication Appropriateness Index (MAI) + AGS Beers 2023.
**Framing — REGIMEN-LEVEL, ANTI-DOUBLE-COUNT:** Scores the regimen as a whole (count, Beers-listed agents, duplications, unclear indications), NOT the individual drug-disease risks already captured in Modules 1–4. A drug already scored for its mechanism elsewhere scores here only for a *distinct* appropriateness fact (e.g., being Beers-listed).

| Trigger | Points | Source |
|---|---|---|
| ≥10 medications (hyperpolypharmacy) | 5 | MAI; Beers scope |
| ≥1 Beers-listed potentially-inappropriate medication | 4 | Beers 2023 |
| Duplicate therapeutic class | 3 | MAI |
| Medication with unclear/undocumented indication | 3 | MAI |
| 5–9 medications (standard polypharmacy) | 2 | Beers 2023 |

**Tiers (raw):** 0–4 = LOW · 5–9 = MODERATE · 10–15 = HIGH

**Velma:** polypharmacy(6) 2 + glipizide Beers-listed 4 + semaglutide unclear indication 3 = **9 → 9/15 → MODERATE**. (Glipizide scores here for *being Beers-listed*, not again for hypoglycemia mechanism — that was Module 1.)

---

## 8. MODULE 6 — Drug Interactions & Clinical Urgency (max 10)

**Anchor:** Lexicomp/Micromedex-style severity tiers + clinical urgency signals.
**Framing — SMALLEST BY DESIGN:** Captures specific drug-drug interactions and acute urgency (recent harm, active symptoms) not represented elsewhere. Most of ACHOO's signal lives in Modules 1–5.

| Trigger | Points | Source |
|---|---|---|
| Major/contraindicated drug-drug interaction | 4 | Lexicomp/Micromedex-style |
| Recent ED visit / hospitalization (~90 days) | 3 | Karter; clinical urgency |
| Active symptomatic adverse effect (dizziness, confusion, bleeding) | 2 | Clinical urgency |
| Recent medication change (~30 days) | 1 | Clinical consensus |

**Double-count caveat:** insulin+sulfonylurea additive hypoglycemia is largely captured in Module 1. Score it here only as a *named major interaction* (clinician's judgment: 0 for strict no-double-count, or up to 2 to document the named interaction). Velma example uses 2.

**Tiers (raw):** 0–3 = LOW · 4–6 = MODERATE · 7–10 = HIGH

**Velma:** named interaction 2 + prior ED visit 3 + dizziness 2 = **7 → 7/10 → HIGH**

---

## 9. Composite layer — reasoning across modules

**This entire layer is EXPERT-DEFINED REASONING, not a validated instrument. Label it as such everywhere.**

ACHOO does **not** sum module scores into one number (that would double-count shared drivers and hide interactions). Instead, four layers:

### Layer 1 — Independent module reporting
Report each module's capped score and tier as-is. No blending.

### Layer 2 — Shared-driver detection
Scan which medications load more than one module. No scoring — just naming. Shared drivers are the highest-value deprescribing targets because one change helps multiple domains. Requires a drug→pathway mapping (see Section 11).

### Layer 3 — Compounding interaction flag
Raise a flag when (a) ≥2 modules are HIGH (or MODERATE+) AND (b) they are mechanistically linked OR share a driver.
**Defined mechanistic links (expert-defined):**
- Hypoglycemia → Falls (hypoglycemic episode is a direct fall mechanism)
- Renal/dehydration → Falls (volume depletion → orthostasis)
- Renal/dehydration → Hypoglycemia (impaired drug clearance)
- Nutrition (GLP-1) → Hypoglycemia (appetite suppression → erratic intake)

### Layer 4 — Overall tier (rule, never a sum)
```
overall_tier = highest individual module tier
if compounding_flag fires: escalate one level (capped at HIGH)
```

---

## 10. Velma — complete worked output

| Module | Score | Tier |
|---|---|---|
| 1. Hypoglycemia | 25/25 | HIGH |
| 2. Falls & Orthostasis | 16/20 | HIGH |
| 3. Renal & Dehydration | 8/15 | MODERATE |
| 4. GLP-1/Frailty/Nutrition | 7/15 | MODERATE |
| 5. Polypharmacy/Appropriateness | 9/15 | MODERATE |
| 6. Interactions & Urgency | 7/10 | HIGH |

**Shared drivers:** hydrochlorothiazide (hypoglycemia + falls + renal); poor oral intake (hypoglycemia + falls + nutrition)
**Compounding flags:** hypo↔falls; nutrition→hypo; renal→hypo
**Overall: HIGH / URGENT — multi-domain compounding**

**Headline recommendation (the thesis of ACHOO):**
> Mrs. Velma Johnson is HIGH-risk across hypoglycemia, falls, and clinical urgency, with moderate renal, nutrition, and appropriateness concerns — and these domains compound rather than stack. Two medications drive cross-system harm: **hydrochlorothiazide** (hypoglycemia + falls + renal volume) is the single highest-value deprescribing target; **glipizide** (hypoglycemia + Beers-inappropriate) is second. One carries an unresolved unknown: **semaglutide** — establish indication, as glucose-lowering-only use would be overtreatment at A1c 6.4. Two are protective and should NOT be deprescribed for these flags: **empagliflozin** and **lisinopril** (renally protective per KDIGO). Pharmacist priority: (1) HCTZ review, (2) glipizide deprescribe/reduce, (3) establish semaglutide indication, (4) reassess A1c target — 6.4 is too tight for a frail elder on insulin. **Human pharmacist review required before any change.**

---

## 11. Drug → pathway mapping (needed for shared-driver detection)

Implementation needs to know which module pathway(s) each drug loads. Demo-scale example:

| Drug | Hypoglycemia | Falls | Renal | Nutrition | Appropriateness |
|---|---|---|---|---|---|
| glipizide | ✓ | — | (cleared) | — | Beers-listed |
| insulin glargine | ✓ | — | (cleared) | — | — |
| hydrochlorothiazide | (volume) | ✓ | ✓ volume | — | — |
| lisinopril | — | ✓ orthostasis | ✓ PROTECTIVE | — | — |
| empagliflozin | — | — | ✓ PROTECTIVE | — | — |
| semaglutide | (via intake) | — | — | ✓ | unclear indication |

At scale this becomes a real knowledge-base task; for a demo set it is hand-mappable.

---

## 12. Required audit-trail / storage format

Every assessment stores (this is the human-readable form; mirror as structured fields):

```
Patient ID: SYN-001
Assessment date: [ISO date]
─── MODULE RESULTS ───
Hypoglycemia Risk: 25/25 — HIGH
Falls & Orthostasis: 16/20 — HIGH
Renal & Dehydration: 8/15 — MODERATE
GLP-1/Frailty/Nutrition: 7/15 — MODERATE
Polypharmacy/Appropriateness: 9/15 — MODERATE
Interactions & Urgency: 7/10 — HIGH
─── PER-FACTOR EVIDENCE TRAIL ───
[factor, points, source, plain-language explanation] for every triggered factor
─── FACTORS UNKNOWN / MISSING ───
[list, or "None"]
─── COMPOSITE ANALYSIS ───
Shared drivers: hydrochlorothiazide (hypo+falls+renal); poor intake (hypo+falls+nutrition)
Compounding flag: YES — hypo↔falls, nutrition→hypo, renal→hypo
Overall tier: HIGH / URGENT (compounding)
Protective — do NOT deprescribe for these flags: empagliflozin, lisinopril
Highest-value interventions: 1) HCTZ review  2) glipizide deprescribe/reduce  3) establish semaglutide indication  4) reassess A1c target
─── METHODOLOGY ───
Modules: evidence-anchored (Karter, Beers, STOPP/START, STOPPFall, KDIGO, ADA, MAI)
Composite layer + weights: expert-defined clinical reasoning, NOT a validated multi-domain instrument
─── GOVERNANCE ───
Human-in-the-loop: Pharmacist review required before any medication change
```

---

## 13. System-prompt logic (portable, framework-agnostic)

The agent, given a patient case, must:
1. Review age, conditions, medications, labs, renal function, clinical flags.
2. Apply each module's scoring rules exactly; score only clearly-supported factors; never invent missing data.
3. For each module: list triggered factors with points + source, compute raw, cap to max, assign tier from raw.
4. Run composite layers 1–4 (shared-driver detection, compounding flag, overall tier).
5. Produce: per-module results, per-factor evidence trail, factors-unknown list, composite analysis, prioritized pharmacist action plan, follow-up timeline, and the audit-trail block.
6. State the methodology distinction (validated modules vs. expert-defined composite) every time.
7. End every output with: pharmacist review required before any medication change. Never diagnose, prescribe, or autonomously change therapy.

**Missing-data rules:** if A1c absent → "A1c not available — unable to assess overtight-control trigger." If renal function absent → "Renal function not available — unable to assess CKD trigger." If meal pattern absent → do not trigger poor intake. If prior hypoglycemia not described → do not trigger that factor. If medication list may be incomplete → "Medication list may be incomplete — pharmacist verification recommended."

---

## 14. Honesty checklist (apply to every output, demo, and write-up)

- [ ] Modules labeled as evidence-anchored; composite labeled as expert-defined reasoning
- [ ] No claim that the composite score is "validated" or "predictive"
- [ ] Protective drugs (SGLT2, ACE/ARB) credited, not penalized
- [ ] Missing data stated as missing, never invented
- [ ] Drug + symptom pairings respected (not blanket drug penalties)
- [ ] No double-counting of the same mechanism across modules
- [ ] Every output ends with human-in-the-loop pharmacist review
- [ ] All classifications flagged for verification against current guidelines

---

## 15. Roadmap notes (beyond the demo)

- **Validation:** the composite layer (weights, compounding logic, escalation rule) is the part that would need prospective validation against real outcomes (falls, hypoglycemia events, ED visits) before any real clinical use. Modules borrow others' validation; the composite is ACHOO's own and unvalidated.
- **Knowledge base:** the drug→pathway map (Section 11) is trivial at demo scale and a substantial maintained dataset at real scale.
- **Heaviest module to build:** Module 3 (three sub-assessments + appropriateness engine).
- **Where ACHOO fits:** MTM workflows, geriatric medication review, deprescribing support — always as pharmacist augmentation, never replacement.

---

*ACHOO clinical scoring specification v1.0. Synthetic data only. Not a medical device. All classifications require verification against current published guidelines by a licensed pharmacist before clinical use.*