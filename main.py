import os
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from dotenv import load_dotenv
from flask import Flask, jsonify
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from achoo.scoring import score_patient

load_dotenv()

app = Flask(__name__)

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB", "achoo")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "patients")

mongo_client = None
patients_collection = None

if MONGO_URI:
    try:
        mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = mongo_client[MONGO_DB]
        patients_collection = db[MONGO_COLLECTION]
    except PyMongoError:
        mongo_client = None
        patients_collection = None


def make_json_safe(value: Any) -> Any:
    """Convert MongoDB/ObjectId/date values into JSON-safe values."""
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: make_json_safe(val) for key, val in value.items()}
    if isinstance(value, list):
        return [make_json_safe(item) for item in value]
    return value


def get_mongo_collection():
    """Return the MongoDB collection or None if MongoDB is not configured."""
    if not MONGO_URI or patients_collection is None:
        return None
    return patients_collection


def velma_patient() -> dict:
    """Synthetic demo patient from the ACHOO clinical scoring specification."""
    return {
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


@app.route("/health", methods=["GET"])
def health():
    return jsonify(
        {
            "status": "ok",
            "service": "ACHOO",
            "message": "ACHOO medication safety triage API is running",
            "mongodb_configured": bool(MONGO_URI),
        }
    )


@app.route("/demo/velma", methods=["GET"])
def demo_velma():
    return jsonify(velma_patient())


@app.route("/assess/velma", methods=["POST"])
def assess_velma():
    assessment = score_patient(velma_patient())
    return jsonify(make_json_safe(assessment))


@app.route("/patient/<patient_id>", methods=["GET"])
def get_patient(patient_id: str):
    collection = get_mongo_collection()
    if collection is None:
        return (
            jsonify(
                {
                    "error": "MongoDB is not configured.",
                    "message": "Check that MONGO_URI, MONGO_DB, and MONGO_COLLECTION are set in .env.",
                }
            ),
            500,
        )

    try:
        patient = collection.find_one({"patient_id": patient_id})
    except PyMongoError as exc:
        return jsonify({"error": "MongoDB read failed.", "details": str(exc)}), 500

    if patient is None:
        return jsonify({"error": "Patient not found.", "patient_id": patient_id}), 404

    return jsonify(make_json_safe(patient))


@app.route("/assess/<patient_id>", methods=["POST"])
def assess_patient(patient_id: str):
    collection = get_mongo_collection()
    if collection is None:
        return (
            jsonify(
                {
                    "error": "MongoDB is not configured.",
                    "message": "Check that MONGO_URI, MONGO_DB, and MONGO_COLLECTION are set in .env.",
                }
            ),
            500,
        )

    try:
        patient = collection.find_one({"patient_id": patient_id})
    except PyMongoError as exc:
        return jsonify({"error": "MongoDB read failed.", "details": str(exc)}), 500

    if patient is None:
        return jsonify({"error": "Patient not found.", "patient_id": patient_id}), 404

    patient_for_scoring = make_json_safe(patient)
    assessment = score_patient(patient_for_scoring)
    assessment["assessment_date"] = datetime.now(timezone.utc).isoformat()

    try:
        collection.update_one(
            {"patient_id": patient_id},
            {
                "$set": {
                    "achoo_assessment": assessment,
                    "achoo_assessment_updated_at": datetime.now(timezone.utc),
                }
            },
        )
    except PyMongoError as exc:
        return jsonify({"error": "MongoDB write-back failed.", "details": str(exc)}), 500

    return jsonify(make_json_safe(assessment))


if __name__ == "__main__":
    app.run(debug=True)