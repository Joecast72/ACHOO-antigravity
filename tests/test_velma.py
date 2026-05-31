import pytest
from achoo.scoring import score_patient

def test_velma_johnson():
    patient = {
        "patient_id": "SYN-001",
        "age": 78,
        "conditions": ["Type 2 Diabetes", "CKD Stage 3", "Fall history"],
        "labs": {
            "a1c": 6.4,
            "egfr": 42
        },
        "medications": ["glipizide", "insulin glargine", "semaglutide", "empagliflozin", "hydrochlorothiazide", "lisinopril"],
        "flags": ["recent fall", "dizziness", "poor appetite", "prior hypoglycemia ED visit"]
    }
    
    result = score_patient(patient)
    
    # Assert top-level structure
    assert result["patient_id"] == "SYN-001"
    assert "assessment_date" in result
    assert result["overall_tier"] == "HIGH / URGENT (compounding)"
    
    # Assert module scores and tiers
    m_res = result["module_results"]
    
    # 1. Hypoglycemia
    assert m_res["hypoglycemia_risk"]["raw_score"] == 34
    assert m_res["hypoglycemia_risk"]["capped_score"] == 25
    assert m_res["hypoglycemia_risk"]["tier"] == "HIGH"
    
    # 2. Falls & Orthostasis
    assert m_res["falls_risk"]["raw_score"] == 16
    assert m_res["falls_risk"]["capped_score"] == 16
    assert m_res["falls_risk"]["tier"] == "HIGH"
    
    # 3. Renal & Dehydration
    assert m_res["renal_risk"]["raw_score"] == 8
    assert m_res["renal_risk"]["capped_score"] == 8
    assert m_res["renal_risk"]["tier"] == "MODERATE"
    
    # 4. Nutrition
    assert m_res["nutrition_risk"]["raw_score"] == 7
    assert m_res["nutrition_risk"]["capped_score"] == 7
    assert m_res["nutrition_risk"]["tier"] == "MODERATE"
    
    # 5. Polypharmacy
    assert m_res["polypharmacy_risk"]["raw_score"] == 9
    assert m_res["polypharmacy_risk"]["capped_score"] == 9
    assert m_res["polypharmacy_risk"]["tier"] == "MODERATE"
    
    # 6. Interactions
    assert m_res["interactions_urgency"]["raw_score"] == 7
    assert m_res["interactions_urgency"]["capped_score"] == 7
    assert m_res["interactions_urgency"]["tier"] == "HIGH"
    
    # Assert shared drivers
    assert any("hydrochlorothiazide" in sd for sd in result["shared_drivers"])
    assert any("glipizide" in sd for sd in result["shared_drivers"])
    assert any("semaglutide" in sd for sd in result["shared_drivers"])
    assert any("poor oral intake" in sd for sd in result["shared_drivers"])
    assert any("dizziness" in sd for sd in result["shared_drivers"])
    
    # Assert compounding flags
    assert "hypo ↔ falls" in result["compounding_flags"]
    assert "nutrition (GLP-1) → hypoglycemia" in result["compounding_flags"]
    assert "renal/dehydration → hypoglycemia" in result["compounding_flags"]
    assert "renal/dehydration ↔ falls" in result["compounding_flags"]
    
    # Assert governance note rule
    assert result["governance_note"].endswith("Pharmacist review required before any medication change.")

def test_missing_data():
    patient = {
        "patient_id": "SYN-002",
        "age": 70,
        "conditions": [],
        "labs": {},
        "medications": [],
        "flags": []
    }
    
    result = score_patient(patient)
    assert len(result["missing_or_unknown_factors"]) > 0
    assert "A1c not available" in "".join(result["missing_or_unknown_factors"])
    assert "Renal function not available" in "".join(result["missing_or_unknown_factors"])
