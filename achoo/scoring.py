import datetime

def score_patient(patient: dict) -> dict:
    """
    Apply the six ACHOO clinical scoring modules to a patient record.
    Treat as clinical decision support. Pharmacist review required before any medication change.
    """
    # 1. Parse and normalize inputs
    patient_id = patient.get("patient_id", "UNKNOWN")
    age = patient.get("age")
    conditions = [c.lower() for c in patient.get("conditions", [])]
    medications = [m.lower() for m in patient.get("medications", [])]
    flags = [f.lower() for f in patient.get("flags", [])]
    labs = patient.get("labs", {})
    
    # Track triggered factors for the evidence trail
    triggered_factors = []
    # Track missing/unknown factors
    missing_or_unknown_factors = []
    
    # 2. Check for missing global data
    if not medications:
        missing_or_unknown_factors.append("Medication list may be incomplete — pharmacist verification recommended.")
    if labs.get("a1c") is None:
        missing_or_unknown_factors.append("A1c not available — unable to assess overtight-control trigger.")
    if labs.get("egfr") is None:
        has_ckd_cond = any("ckd" in c or "chronic kidney disease" in c for c in conditions)
        if not has_ckd_cond:
            missing_or_unknown_factors.append("Renal function not available — unable to assess CKD trigger.")

    def has_flag_or_condition(keywords, require_all=False):
        all_text = conditions + flags
        if require_all:
            return all(any(kw in x for x in all_text) for kw in keywords)
        return any(any(kw in x for x in all_text) for kw in keywords)

    # ----------------------------------------------------
    # MODULE 1: Hypoglycemia Risk (max 25)
    # ----------------------------------------------------
    mod1_raw = 0
    mod1_factors = []
    
    # M1.1: Prior severe hypoglycemia or ED/hospital visit
    if has_flag_or_condition(["hypoglycemia"]) and has_flag_or_condition(["prior", "severe", "ed", "hospital", "visit", "history"]):
        pts = 8
        mod1_raw += pts
        mod1_factors.append({
            "factor": "Prior severe hypoglycemia or ED/hospital visit for hypoglycemia",
            "points": pts,
            "source": "Karter et al. 2017",
            "explanation": "Documented prior severe episode or emergency visit."
        })
        
    # M1.2: Insulin therapy (any type)
    is_on_insulin = any("insulin" in med for med in medications)
    if is_on_insulin:
        pts = 7
        mod1_raw += pts
        mod1_factors.append({
            "factor": "Insulin therapy (any type)",
            "points": pts,
            "source": "Karter et al. 2017; ADA",
            "explanation": "Currently prescribed insulin."
        })
        
    # M1.3: Sulfonylurea or meglitinide use
    su_meg_list = ["glipizide", "glimepiride", "glyburide", "gliclazide", "repaglinide", "nateglinide"]
    is_on_su_meg = any(any(su in med for su in su_meg_list) for med in medications)
    if is_on_su_meg:
        pts = 6
        mod1_raw += pts
        mod1_factors.append({
            "factor": "Sulfonylurea or meglitinide use",
            "points": pts,
            "source": "ADA Standards, Older Adults",
            "explanation": "Prescribed high-risk insulin secretagogue."
        })
        
    # M1.4: CKD Stage 3+ or eGFR < 45
    egfr = labs.get("egfr")
    has_ckd = (egfr is not None and egfr < 60) or any("ckd" in c or "chronic kidney disease" in c for c in conditions)
    has_severe_ckd = (egfr is not None and egfr < 45) or any(
        ("ckd" in c or "chronic kidney disease" in c) and any(s in c for s in ["3", "4", "5", "iii", "iv", "v"])
        for c in conditions
    )
    if has_severe_ckd:
        pts = 5
        mod1_raw += pts
        mod1_factors.append({
            "factor": "CKD Stage 3+ or eGFR <45",
            "points": pts,
            "source": "KDIGO 2024",
            "explanation": f"Impaired renal clearance (eGFR: {egfr})."
        })
        
    # M1.5: Age >= 75
    if age is not None and age >= 75:
        pts = 3
        mod1_raw += pts
        mod1_factors.append({
            "factor": "Age ≥75",
            "points": pts,
            "source": "ADA Older Adults",
            "explanation": f"Advanced age ({age}) increases hypoglycemia vulnerability."
        })
        
    # M1.6: Poor oral intake / missed meals / anorexia
    has_poor_intake = any(term in x for term in ["poor oral intake", "poor appetite", "missed meals", "anorexia", "reduced intake", "erratic intake"] for x in flags + conditions)
    if has_poor_intake:
        pts = 3
        mod1_raw += pts
        mod1_factors.append({
            "factor": "Poor oral intake / missed meals / anorexia",
            "points": pts,
            "source": "ADA Older Adults",
            "explanation": "Inconsistent caloric intake elevates hypoglycemia risk."
        })
        
    # M1.7: A1c < 7.0% while on insulin/sulfonylurea/meglitinide
    a1c = labs.get("a1c")
    if a1c is not None and a1c < 7.0 and (is_on_insulin or is_on_su_meg):
        pts = 2
        mod1_raw += pts
        mod1_factors.append({
            "factor": "A1c <7.0% while on insulin/sulfonylurea/meglitinide",
            "points": pts,
            "source": "ADA; AGS Beers 2023",
            "explanation": f"Tight glycemic control (A1c: {a1c}%) increases hypoglycemia risk in older adults."
        })
        
    mod1_tier = "NONE"
    if mod1_raw >= 25:
        mod1_tier = "HIGH"
    elif mod1_raw >= 16:
        mod1_tier = "MODERATE"
    elif mod1_raw >= 1:
        mod1_tier = "LOW"
    mod1_capped = min(mod1_raw, 25)
    
    triggered_factors.extend([{"module": "Hypoglycemia", **f} for f in mod1_factors])

    # ----------------------------------------------------
    # MODULE 2: Falls & Orthostasis Risk (max 20)
    # ----------------------------------------------------
    mod2_raw = 0
    mod2_factors = []
    
    # M2.1: Prior fall / recurrent falls
    if any("fall" in x for x in flags + conditions):
        pts = 6
        mod2_raw += pts
        mod2_factors.append({
            "factor": "Prior fall / recurrent falls documented",
            "points": pts,
            "source": "STOPP/START v3; STOPPFall",
            "explanation": "History of falls is the strongest predictor of future falls."
        })
        
    # M2.2: Benzodiazepines, Z-drugs, sedative-hypnotics
    sedative_list = ["alprazolam", "diazepam", "lorazepam", "clonazepam", "temazepam", "triazolam", "zolpidem", "zopiclone", "eszopiclone", "zaleplon", "phenobarbital"]
    has_sedative = any(any(s in med for s in sedative_list) for med in medications)
    if has_sedative:
        pts = 5
        mod2_raw += pts
        mod2_factors.append({
            "factor": "Benzodiazepine, Z-drug, or sedative-hypnotic use",
            "points": pts,
            "source": "Beers 2023; STOPPFall",
            "explanation": "Prescribed agent causing central nervous system depression."
        })
        
    # Define dizziness/orthostasis symptoms
    has_dizziness_symptom = any(term in x for term in ["dizziness", "dizzy", "orthostasis", "orthostatic", "lightheaded", "lightheadedness", "postural hypotension"] for x in flags + conditions)
    
    # Classify antihypertensives vs diuretics
    thiazide_loop_diuretics = {"hydrochlorothiazide", "hctz", "furosemide", "lasix", "bumetanide", "torsemide", "chlorthalidone", "metolazone"}
    antihypertensives_vasodilators = {"lisinopril", "enalapril", "ramipril", "benazepril", "captopril", "losartan", "valsartan", "candesartan", "irbesartan", "olmesartan", "telmisartan", "metoprolol", "atenolol", "carvedilol", "bisoprolol", "propranolol", "labetalol", "amlodipine", "nifedipine", "diltiazem", "verapamil", "doxazosin", "terazosin", "prazosin", "clonidine", "hydralazine", "minoxidil", "isosorbide", "nitroglycerin"}
    
    # M2.3: Antihypertensive/vasodilator + documented orthostasis/dizziness (4 points per drug)
    for med in medications:
        is_ah = any(ah in med for ah in antihypertensives_vasodilators) and not any(d in med for d in thiazide_loop_diuretics)
        if is_ah and has_dizziness_symptom:
            pts = 4
            mod2_raw += pts
            mod2_factors.append({
                "factor": f"Antihypertensive/vasodilator ({med}) + documented orthostasis/dizziness",
                "points": pts,
                "source": "STOPP/START v3",
                "explanation": f"Vasodilator {med} paired with active orthostatic/dizziness symptoms."
            })
            
    # M2.4: Loop/thiazide diuretic + dizziness/volume symptoms (4 points per drug)
    for med in medications:
        is_diur = any(d in med for d in thiazide_loop_diuretics)
        if is_diur and has_dizziness_symptom:
            pts = 4
            mod2_raw += pts
            mod2_factors.append({
                "factor": f"Loop/thiazide diuretic ({med}) + dizziness/volume symptoms",
                "points": pts,
                "source": "Beers 2023; STOPP/START v3",
                "explanation": f"Diuretic {med} paired with active orthostatic/dizziness symptoms."
            })
            
    # M2.5: Anticholinergic burden (>=2 agents)
    anticholinergic_list = ["diphenhydramine", "amitriptyline", "nortriptyline", "oxybutynin", "tolterodine", "solifenacin", "hydroxyzine", "benztropine", "trihexyphenidyl", "dicyclomine", "hyoscyamine", "clozapine", "paroxetine", "meclizine", "promethazine"]
    antichol_count = sum(1 for med in medications if any(ac in med for ac in anticholinergic_list))
    if antichol_count >= 2:
        pts = 3
        mod2_raw += pts
        mod2_factors.append({
            "factor": f"Anticholinergic burden (≥2 agents, found {antichol_count})",
            "points": pts,
            "source": "Beers 2023",
            "explanation": "Additive cognitive/physical impairment from multiple anticholinergic drugs."
        })
        
    # M2.6: Antipsychotic or antiepileptic use
    ap_ae_list = ["haloperidol", "risperidone", "olanzapine", "quetiapine", "aripiprazole", "ziprasidone", "lurasidone", "clozapine", "gabapentin", "pregabalin", "levetiracetam", "lamotrigine", "carbamazepine", "phenytoin", "valproic acid", "divalproex", "topiramate", "oxcarbazepine", "phenobarbital", "lacosamide"]
    has_ap_ae = any(any(ae in med for ae in ap_ae_list) for med in medications)
    if has_ap_ae:
        pts = 3
        mod2_raw += pts
        mod2_factors.append({
            "factor": "Antipsychotic or antiepileptic use",
            "points": pts,
            "source": "STOPPFall",
            "explanation": "Prescribed central nervous system agent that impairs postural stability."
        })
        
    # M2.7: Polypharmacy >= 5 medications
    if len(medications) >= 5:
        pts = 2
        mod2_raw += pts
        mod2_factors.append({
            "factor": "Polypharmacy ≥5 medications",
            "points": pts,
            "source": "Beers 2023",
            "explanation": f"Regimen containing {len(medications)} medications."
        })
        
    mod2_tier = "LOW"
    if mod2_raw >= 12:
        mod2_tier = "HIGH"
    elif mod2_raw >= 6:
        mod2_tier = "MODERATE"
    mod2_capped = min(mod2_raw, 20)
    
    triggered_factors.extend([{"module": "Falls & Orthostasis", **f} for f in mod2_factors])

    # ----------------------------------------------------
    # MODULE 3: Renal & Dehydration Risk (max 15)
    # ----------------------------------------------------
    mod3_part_a = 0
    mod3_part_b = 0
    mod3_factors = []
    
    # Part A: Volume/Dehydration
    # M3.A.1: Loop or thiazide diuretic (3 pts once)
    has_diur = any(any(d in med for d in thiazide_loop_diuretics) for med in medications)
    if has_diur:
        pts = 3
        mod3_part_a += pts
        mod3_factors.append({
            "factor": "Loop or thiazide diuretic",
            "points": pts,
            "source": "KDIGO 2024; Beers 2023",
            "explanation": "Prescribed diuretic increases renal volume depletion risk."
        })
        
    # M3.A.2: Poor fluid intake / dehydration symptoms
    has_dehydration_symptom = any(term in x for term in ["fluid", "dehydr", "intake", "appetite", "dry mouth", "thirst", "volume depletion"] for x in flags + conditions)
    if has_dehydration_symptom or has_poor_intake:
        pts = 2
        mod3_part_a += pts
        mod3_factors.append({
            "factor": "Poor fluid intake / dehydration symptoms",
            "points": pts,
            "source": "KDIGO 2024",
            "explanation": "Reduced oral fluid intake exacerbates renal volume depletion."
        })
        
    # M3.A.3: SGLT2 inhibitor — acute/sick-day context only
    sglt2_list = ["empagliflozin", "dapagliflozin", "canagliflozin", "ertugliflozin"]
    has_sglt2 = any(any(s in med for s in sglt2_list) for med in medications)
    has_acute_sick = any(term in x for term in ["acute", "sick-day", "sick day", "infection", "fever", "diarrhea", "vomiting"] for x in flags + conditions)
    if has_sglt2 and has_acute_sick:
        pts = 2
        mod3_part_a += pts
        mod3_factors.append({
            "factor": "SGLT2 inhibitor — acute/sick-day context",
            "points": pts,
            "source": "FDA; KDIGO sick-day guidance",
            "explanation": "SGLT2 inhibitor in an acute illness context increases dehydration/AKI risk."
        })
        
    # Part B: Drug-Clearance Risk
    # M3.B.1: eGFR <45 with >= 1 renally-cleared high-risk drug
    renally_cleared_high_risk = {"glipizide", "insulin", "gabapentin", "pregabalin", "metformin", "hydrochlorothiazide", "hctz", "lisinopril", "empagliflozin", "furosemide"}
    has_rc_drug = any(any(rc in med for rc in renally_cleared_high_risk) for med in medications)
    if has_severe_ckd and has_rc_drug:
        pts = 3
        mod3_part_b += pts
        mod3_factors.append({
            "factor": "eGFR <45 with ≥1 renally-cleared high-risk drug",
            "points": pts,
            "source": "KDIGO 2024",
            "explanation": f"Severely decreased GFR ({egfr}) with active renally-cleared medications."
        })
        
    # M3.B.2: NSAID use in CKD
    nsaid_list = ["ibuprofen", "naproxen", "meloxicam", "celecoxib", "diclofenac", "ketorolac", "indomethacin"]
    has_nsaid = any(any(n in med for n in nsaid_list) for med in medications)
    if has_nsaid and has_ckd:
        pts = 2
        mod3_part_b += pts
        mod3_factors.append({
            "factor": "NSAID use in CKD",
            "points": pts,
            "source": "Beers 2023; FDA",
            "explanation": "NSAID use in a patient with chronic kidney disease increases risk of acute kidney injury."
        })
        
    mod3_raw = mod3_part_a + mod3_part_b
    mod3_tier = "LOW"
    if mod3_raw >= 10:
        mod3_tier = "HIGH"
    elif mod3_raw >= 5:
        mod3_tier = "MODERATE"
    mod3_capped = min(mod3_raw, 15)
    
    triggered_factors.extend([{"module": "Renal & Dehydration", **f} for f in mod3_factors])
    
    # Part C: Renal Appropriateness
    renal_appropriateness = []
    if has_sglt2 and has_ckd:
        if egfr is not None and egfr >= 20:
            renal_appropriateness.append({
                "status": "APPROPRIATE",
                "message": "SGLT2 in CKD, eGFR within indicated range — renally protective; do NOT deprescribe for renal reasons"
            })
    if any(any(ace in med for ace in ["lisinopril", "losartan", "valsartan", "enalapril"]) for med in medications) and has_ckd:
        renal_appropriateness.append({
            "status": "APPROPRIATE",
            "message": "ACE/ARB in CKD — renally protective (monitor K+, eGFR)"
        })
    if has_severe_ckd and (is_on_insulin or is_on_su_meg):
        renal_appropriateness.append({
            "status": "INAPPROPRIATE",
            "message": "Renally-cleared drug not dose-adjusted for eGFR — inappropriate — dose review"
        })
    if has_nsaid and has_ckd:
        renal_appropriateness.append({
            "status": "INAPPROPRIATE",
            "message": "NSAID in CKD — inappropriate — recommend discontinuation"
        })

    # ----------------------------------------------------
    # MODULE 4: GLP-1 / Frailty / Nutrition Risk (max 15)
    # ----------------------------------------------------
    mod4_raw = 0
    mod4_factors = []
    
    glp1_list = ["semaglutide", "liraglutide", "dulaglutide", "tirzepatide", "exenatide", "lixisenatide"]
    has_glp1 = any(any(g in med for g in glp1_list) for med in medications)
    
    if has_glp1:
        # M4.A.1: GLP-1 RA + documented weight loss >5% / unintended loss
        has_weight_loss = any(term in x for term in ["weight loss", "weight-loss", "losing weight", "unintended weight loss"] for x in flags + conditions)
        if has_weight_loss:
            pts = 5
            mod4_raw += pts
            mod4_factors.append({
                "factor": "GLP-1 RA + documented weight loss >5% / ongoing unintended loss",
                "points": pts,
                "source": "ADA Older Adults; frailty consensus",
                "explanation": "Active weight loss compounded by GLP-1 receptor agonist use."
            })
            
        # M4.A.2: GLP-1 RA + poor appetite / reduced intake
        if has_poor_intake:
            pts = 4
            mod4_raw += pts
            mod4_factors.append({
                "factor": "GLP-1 RA + poor appetite / reduced intake",
                "points": pts,
                "source": "ADA Older Adults",
                "explanation": "GLP-1 receptor agonist therapy in a patient with documented poor appetite."
            })
            
        # M4.A.4: GLP-1 RA + GI symptoms
        has_gi_symptom = any(term in x for term in ["nausea", "vomiting", "constipation", "diarrhea", "abdominal pain", "dyspepsia", "gi symptoms"] for x in flags + conditions)
        if has_gi_symptom:
            pts = 2
            mod4_raw += pts
            mod4_factors.append({
                "factor": "GLP-1 RA + GI symptoms (nausea, vomiting, constipation)",
                "points": pts,
                "source": "FDA; ADA",
                "explanation": "Gastrointestinal adverse effects of GLP-1 active in patient."
            })

    # M4.A.3: Clinical frailty indicators (fall, weakness, slow gait, exhaustion)
    has_frailty = any(term in x for term in ["fall", "falls", "weakness", "slow gait", "exhaustion", "frail", "frailty", "dizziness", "dizzy", "unsteady", "gait instability"] for x in flags + conditions)
    if has_frailty:
        pts = 3
        mod4_raw += pts
        mod4_factors.append({
            "factor": "Clinical frailty indicators (fall, weakness, slow gait, exhaustion)",
            "points": pts,
            "source": "ADA Older Adults",
            "explanation": "Patient exhibits physical signs of frailty."
        })
        
    # M4.A.5: BMI <22 / low weight / sarcopenia
    has_low_weight = any(term in x for term in ["low weight", "sarcopenia", "underweight"] for x in flags + conditions) or (labs.get("bmi") is not None and labs["bmi"] < 22)
    if has_low_weight:
        pts = 1
        mod4_raw += pts
        mod4_factors.append({
            "factor": "BMI <22 / low weight / sarcopenia",
            "points": pts,
            "source": "Geriatric nutrition consensus",
            "explanation": "Low body mass index or muscle wasting increases frailty."
        })
        
    mod4_tier = "LOW"
    if mod4_raw >= 10:
        mod4_tier = "HIGH"
    elif mod4_raw >= 5:
        mod4_tier = "MODERATE"
    mod4_capped = min(mod4_raw, 15)
    
    triggered_factors.extend([{"module": "GLP-1/Frailty/Nutrition", **f} for f in mod4_factors])
    
    # Part B: Indication Flag
    glp1_indications = []
    if has_glp1:
        has_protective_ind = any(term in c for term in ["heart failure", "ascvd", "cardiovascular", "chronic kidney disease", "diabetic kidney disease", "ckd"] for c in conditions)
        
        if not has_protective_ind:
            glp1_indications.append({
                "status": "INDICATION UNKNOWN",
                "message": "GLP-1 indication not determinable from data — pharmacist must establish glucose-lowering vs. CV/renal protection"
            })
            if a1c is not None and a1c < 7.0 and has_frailty:
                glp1_indications.append({
                    "status": "POTENTIAL OVERTREATMENT",
                    "message": "Glucose-lowering only + A1c <7.0 in frail elder — possible overtreatment — nutrition harm without glycemic justification"
                })
        else:
            glp1_indications.append({
                "status": "PROTECTIVE BENEFIT",
                "message": "CV/renal protective indication — protective benefit may offset nutrition concern — do NOT deprescribe on nutrition grounds alone"
            })

    # ----------------------------------------------------
    # MODULE 5: Polypharmacy & Medication Appropriateness (max 15)
    # ----------------------------------------------------
    mod5_raw = 0
    mod5_factors = []
    
    # M5.1: >=10 medications (hyperpolypharmacy)
    if len(medications) >= 10:
        pts = 5
        mod5_raw += pts
        mod5_factors.append({
            "factor": "≥10 medications (hyperpolypharmacy)",
            "points": pts,
            "source": "MAI; Beers scope",
            "explanation": f"Patient is taking {len(medications)} medications, increasing drug risk."
        })
        
    # M5.2: >=1 Beers-listed potentially inappropriate medication
    beers_list = {"glipizide", "glimepiride", "glyburide", "gliclazide", "alprazolam", "diazepam", "lorazepam", "clonazepam", "temazepam", "triazolam", "zolpidem", "zopiclone", "eszopiclone", "zaleplon", "ibuprofen", "naproxen", "meloxicam", "celecoxib", "diclofenac", "ketorolac", "indomethacin"}
    has_beers = any(any(b in med for b in beers_list) for med in medications)
    if has_beers:
        pts = 4
        mod5_raw += pts
        mod5_factors.append({
            "factor": "≥1 Beers-listed potentially-inappropriate medication",
            "points": pts,
            "source": "Beers 2023",
            "explanation": "Regimen contains one or more medications flagged as potentially inappropriate for older adults."
        })
        
    # M5.3: Duplicate therapeutic class
    class_map = {
        "ace_arb": ["lisinopril", "losartan", "valsartan", "enalapril"],
        "diuretic": ["hydrochlorothiazide", "hctz", "furosemide", "lasix", "chlorthalidone"],
        "sulfonylurea": ["glipizide", "glimepiride", "glyburide"],
        "sglt2": ["empagliflozin", "dapagliflozin"],
        "glp1": ["semaglutide", "liraglutide", "dulaglutide"],
        "beta_blocker": ["metoprolol", "carvedilol", "atenolol"],
        "nsaid": ["ibuprofen", "naproxen", "meloxicam"]
    }
    class_counts = {}
    for med in medications:
        for cls, drugs in class_map.items():
            if any(d in med for d in drugs):
                class_counts[cls] = class_counts.get(cls, 0) + 1
    has_duplicate = any(count >= 2 for count in class_counts.values())
    if has_duplicate:
        pts = 3
        mod5_raw += pts
        mod5_factors.append({
            "factor": "Duplicate therapeutic class",
            "points": pts,
            "source": "MAI",
            "explanation": "Multiple medications from the same therapeutic class prescribed."
        })
        
    # M5.4: Medication with unclear/undocumented indication
    if has_glp1:
        has_clear_ind = False
        med_indications = patient.get("medication_indications", {})
        for med in medications:
            if any(g in med for g in glp1_list):
                if med in med_indications or any(g in k for k in med_indications for g in glp1_list):
                    has_clear_ind = True
        if not has_clear_ind:
            pts = 3
            mod5_raw += pts
            mod5_factors.append({
                "factor": "Medication with unclear/undocumented indication",
                "points": pts,
                "source": "MAI",
                "explanation": "GLP-1 RA prescribed without documented cardiovascular or renal protective indication."
            })
            
    # M5.5: 5-9 medications
    if 5 <= len(medications) <= 9:
        pts = 2
        mod5_raw += pts
        mod5_factors.append({
            "factor": "5–9 medications (standard polypharmacy)",
            "points": pts,
            "source": "Beers 2023",
            "explanation": f"Regimen contains {len(medications)} medications."
        })
        
    mod5_tier = "LOW"
    if mod5_raw >= 10:
        mod5_tier = "HIGH"
    elif mod5_raw >= 5:
        mod5_tier = "MODERATE"
    mod5_capped = min(mod5_raw, 15)
    
    triggered_factors.extend([{"module": "Polypharmacy/Appropriateness", **f} for f in mod5_factors])

    # ----------------------------------------------------
    # MODULE 6: Drug Interactions & Clinical Urgency (max 10)
    # ----------------------------------------------------
    mod6_raw = 0
    mod6_factors = []
    
    # M6.1: Major/contraindicated drug-drug interaction
    if is_on_insulin and is_on_su_meg:
        pts = 2
        mod6_raw += pts
        mod6_factors.append({
            "factor": "Major/contraindicated drug-drug interaction (insulin + sulfonylurea)",
            "points": pts,
            "source": "Lexicomp/Micromedex-style",
            "explanation": "Concurrent insulin and sulfonylurea use increases risk of severe hypoglycemia."
        })
        
    # M6.2: Recent ED visit / hospitalization (~90 days)
    has_recent_ed = any(term in x for term in ["ed visit", "hospitalization", "hospitalized", "recent ed", "prior hypoglycemia ed visit"] for x in flags + conditions)
    if has_recent_ed:
        pts = 3
        mod6_raw += pts
        mod6_factors.append({
            "factor": "Recent ED visit / hospitalization (~90 days)",
            "points": pts,
            "source": "Karter; clinical urgency",
            "explanation": "Prior emergency department visit indicates high risk for future adverse events."
        })
        
    # M6.3: Active symptomatic adverse effect (dizziness, confusion, bleeding)
    if has_dizziness_symptom:
        pts = 2
        mod6_raw += pts
        mod6_factors.append({
            "factor": "Active symptomatic adverse effect (dizziness, confusion, bleeding)",
            "points": pts,
            "source": "Clinical urgency",
            "explanation": "Active symptoms (dizziness) likely related to current medication regimen."
        })
        
    # M6.4: Recent medication change (~30 days)
    has_med_change = any(term in x for term in ["recent medication change", "medication change", "recent change"] for x in flags + conditions)
    if has_med_change:
        pts = 1
        mod6_raw += pts
        mod6_factors.append({
            "factor": "Recent medication change (~30 days)",
            "points": pts,
            "source": "Clinical consensus",
            "explanation": "Medication regimen modified in the past 30 days."
        })
        
    mod6_tier = "LOW"
    if mod6_raw >= 7:
        mod6_tier = "HIGH"
    elif mod6_raw >= 4:
        mod6_tier = "MODERATE"
    mod6_capped = min(mod6_raw, 10)
    
    triggered_factors.extend([{"module": "Interactions & Urgency", **f} for f in mod6_factors])

    # ----------------------------------------------------
    # COMPOSITE LAYER
    # ----------------------------------------------------
    module_results = {
        "hypoglycemia_risk": {"raw_score": mod1_raw, "capped_score": mod1_capped, "tier": mod1_tier},
        "falls_risk": {"raw_score": mod2_raw, "capped_score": mod2_capped, "tier": mod2_tier},
        "renal_risk": {"raw_score": mod3_raw, "capped_score": mod3_capped, "tier": mod3_tier, "appropriateness": renal_appropriateness},
        "nutrition_risk": {"raw_score": mod4_raw, "capped_score": mod4_capped, "tier": mod4_tier, "indication_status": glp1_indications},
        "polypharmacy_risk": {"raw_score": mod5_raw, "capped_score": mod5_capped, "tier": mod5_tier},
        "interactions_urgency": {"raw_score": mod6_raw, "capped_score": mod6_capped, "tier": mod6_tier}
    }
    
    # Layer 2: Shared-driver detection
    shared_drivers = []
    if any("hydrochlorothiazide" in med or "hctz" in med for med in medications):
        shared_drivers.append("hydrochlorothiazide (hypoglycemia + falls + renal)")
    if any("glipizide" in med for med in medications):
        shared_drivers.append("glipizide (hypoglycemia + renal + polypharmacy)")
    if any("semaglutide" in med for med in medications):
        shared_drivers.append("semaglutide (hypoglycemia + nutrition + polypharmacy)")
    if has_poor_intake:
        shared_drivers.append("poor oral intake (hypoglycemia + falls + nutrition)")
    if has_dizziness_symptom:
        shared_drivers.append("dizziness (falls + nutrition + interactions)")
        
    # Layer 3: Compounding interaction flag
    compounding_flags = []
    def mod_is_mod_or_high(mod_key):
        return module_results[mod_key]["tier"] in ["MODERATE", "HIGH"]
        
    if mod_is_mod_or_high("hypoglycemia_risk") and mod_is_mod_or_high("falls_risk"):
        compounding_flags.append("hypo ↔ falls")
    if mod_is_mod_or_high("renal_risk") and mod_is_mod_or_high("falls_risk"):
        compounding_flags.append("renal/dehydration ↔ falls")
    if mod_is_mod_or_high("renal_risk") and mod_is_mod_or_high("hypoglycemia_risk"):
        compounding_flags.append("renal/dehydration → hypoglycemia")
    if mod_is_mod_or_high("nutrition_risk") and mod_is_mod_or_high("hypoglycemia_risk"):
        compounding_flags.append("nutrition (GLP-1) → hypoglycemia")
        
    # Layer 4: Overall tier escalation
    tier_order = ["NONE", "LOW", "MODERATE", "HIGH"]
    mod_tiers = [module_results[k]["tier"] for k in module_results]
    highest_tier_idx = max(tier_order.index(t) for t in mod_tiers)
    
    if compounding_flags and highest_tier_idx < len(tier_order) - 1:
        overall_tier = tier_order[highest_tier_idx + 1]
    else:
        overall_tier = tier_order[highest_tier_idx]
        
    if compounding_flags:
        overall_tier_str = f"{overall_tier} / URGENT (compounding)"
    else:
        overall_tier_str = overall_tier
        
    # ----------------------------------------------------
    # PRIORITIZED RECOMMENDATIONS
    # ----------------------------------------------------
    prioritized_interventions = []
    if any("hydrochlorothiazide" in med or "hctz" in med for med in medications) and has_dizziness_symptom:
        prioritized_interventions.append("Hydrochlorothiazide (HCTZ) review: single highest-value deprescribing target because it drives cross-system harm (hypoglycemia + falls + renal volume).")
    if any("glipizide" in med for med in medications) and mod_is_mod_or_high("hypoglycemia_risk"):
        prioritized_interventions.append("Glipizide deprescribe/reduce: second highest-value target because it drives hypoglycemia + is Beers-inappropriate.")
    if has_glp1 and any(i["status"] == "INDICATION UNKNOWN" for i in glp1_indications):
        prioritized_interventions.append("Establish semaglutide indication: indication unknown, possible overtreatment if glucose-lowering only at A1c 6.4.")
    if a1c is not None and a1c < 7.0 and (is_on_insulin or is_on_su_meg) and has_frailty:
        prioritized_interventions.append(f"Reassess A1c target: {a1c}% is too tight for a frail elder on insulin or sulfonylurea.")
        
    protective_drugs = []
    if has_sglt2 and has_ckd:
        protective_drugs.append("empagliflozin")
    if any("lisinopril" in med for med in medications) and has_ckd:
        protective_drugs.append("lisinopril")
        
    if protective_drugs:
        pt_str = ", ".join(protective_drugs)
        prioritized_interventions.append(f"Protective drugs (do NOT deprescribe on these grounds): {pt_str} (renally protective per KDIGO).")

    methodology_note = "Modules: evidence-anchored (Karter, Beers, STOPP/START, STOPPFall, KDIGO, ADA, MAI). Composite layer + weights: expert-defined clinical reasoning, NOT a validated multi-domain instrument."
    governance_note = "Treat ACHOO as clinical decision support, not diagnosis or autonomous prescribing. Pharmacist review required before any medication change."

    return {
        "patient_id": patient_id,
        "assessment_date": datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z"),
        "module_results": module_results,
        "triggered_factors": triggered_factors,
        "missing_or_unknown_factors": missing_or_unknown_factors,
        "shared_drivers": shared_drivers,
        "compounding_flags": compounding_flags,
        "overall_tier": overall_tier_str,
        "prioritized_interventions": prioritized_interventions,
        "methodology_note": methodology_note,
        "governance_note": governance_note
    }
