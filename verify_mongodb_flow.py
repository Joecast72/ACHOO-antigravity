import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from pymongo import MongoClient

from achoo.scoring import score_patient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB", "achoo")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "patients")

if not MONGO_URI:
    raise RuntimeError("MONGO_URI is not set. Check your .env file.")

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
collection = client[MONGO_DB][MONGO_COLLECTION]

patient_id = "SYN-001"

patient = collection.find_one({"patient_id": patient_id})

if not patient:
    raise RuntimeError(f"Patient {patient_id} not found. Run seed_velma.py first.")

assessment = score_patient(patient)
assessment["assessment_date"] = datetime.now(timezone.utc).isoformat()

collection.update_one(
    {"patient_id": patient_id},
    {
        "$set": {
            "achoo_assessment": assessment,
            "achoo_assessment_updated_at": datetime.now(timezone.utc),
        }
    },
)

updated = collection.find_one({"patient_id": patient_id})

if "achoo_assessment" not in updated:
    raise RuntimeError("Write-back failed: achoo_assessment not found.")

print("ACHOO MongoDB flow verified.")
print(f"Patient ID: {patient_id}")
print(f"Overall tier: {updated['achoo_assessment']['overall_tier']}")
print("MongoDB read → ACHOO scoring → MongoDB write-back: SUCCESS")
print("Pharmacist review required before any medication change.")