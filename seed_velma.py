import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB", "achoo")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "patients")

if not MONGO_URI:
    raise RuntimeError("MONGO_URI is not set. Check your .env file.")

velma = {
    "patient_id": "SYN-001",
    "name": "Mrs. Velma Johnson",
    "age": 78,
    "conditions": ["Type 2 Diabetes", "CKD Stage 3", "Fall history"],
    "labs": {
        "a1c": 6.4,
        "egfr": 42,
    },
    "medications": [
        "glipizide",
        "insulin glargine",
        "semaglutide",
        "empagliflozin",
        "hydrochlorothiazide",
        "lisinopril",
    ],
    "clinical_flags": [
        "recent fall",
        "dizziness",
        "poor appetite",
        "prior hypoglycemia ED visit",
    ],
}

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
collection = client[MONGO_DB][MONGO_COLLECTION]

result = collection.update_one(
    {"patient_id": velma["patient_id"]},
    {"$set": velma},
    upsert=True,
)

print(f"Seeded/updated {velma['patient_id']} in MongoDB.")
print(f"Matched: {result.matched_count}")
print(f"Modified: {result.modified_count}")
print(f"Upserted ID: {result.upserted_id}")