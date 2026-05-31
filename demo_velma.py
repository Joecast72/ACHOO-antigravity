import json
from achoo.scoring import score_patient

def run_demo():
    # Create the synthetic Velma Johnson patient dictionary
    velma = {
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

    # Run the scoring algorithm
    assessment = score_patient(velma)

    # Pretty-print the returned assessment as JSON
    print(json.dumps(assessment, indent=2))

if __name__ == "__main__":
    run_demo()
