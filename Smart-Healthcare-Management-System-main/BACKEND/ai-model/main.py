# main.py
# FastAPI backend for AI Health Chatbot
#
# Designed for:
# - Vercel Python / FastAPI deployment
# - Vercel React/Vite frontend
# - Local development
# - Optional MongoDB
# - Existing model.py subprocess
#
# IMPORTANT:
# Keep model.py and requirements.txt in the same directory as this file.

from pathlib import Path
from typing import Optional
import json
import os
import re
import subprocess
import sys
import threading
import time

import pymongo
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="AI Health Chatbot API",
    version="1.1.0",
    description="AI Health Chatbot API for the Smart Healthcare Management System.",
)


# ============================================================
# CORS
# ============================================================
#
# The browser sends an OPTIONS preflight request before some
# POST requests. CORSMiddleware handles that automatically.
#
# allow_credentials=False is intentional because the chatbot
# endpoint does not require browser cookies.
#
# Allowed origins are configured through the environment. Set one or
# more of the following (comma-separated values are supported):
#
#   FRONTEND_URL=https://<your-frontend-domain>
#   FRONTEND01=https://<your-frontend-domain>
#   FRONTEND02=https://<your-frontend-domain>
#
# Vercel preview deployments such as
# https://<project>-<hash>.vercel.app are also accepted, see
# allow_origin_regex below.
# ============================================================

_frontend_url = os.getenv("FRONTEND_URL", "").strip()

ALLOWED_ORIGINS = {
    origin.strip().rstrip("/")
    for origin in ",".join(
        [
            _frontend_url,
            os.getenv("FRONTEND01", "").strip(),
            os.getenv("FRONTEND02", "").strip(),
            os.getenv("CORS_ALLOWED_ORIGINS", "").strip(),
        ]
    ).split(",")
    if origin.strip()
}

# Local development origins, harmless in production because browsers only
# send them from a machine running the frontend on localhost.
ALLOWED_ORIGINS.update(
    {
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    }
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(ALLOWED_ORIGINS),
    allow_origin_regex=r"^https://[a-zA-Z0-9.-]+\.vercel\.app$",
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Accept", "Content-Type", "Authorization"],
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model.py"


# ============================================================
# MONGODB
# ============================================================
#
# MongoDB is optional for the AI service. The chatbot must still
# work if MongoDB is temporarily unavailable.
#
# Set:
# MONGO_URI=mongodb+srv://...
#
# Optional:
# MONGO_DB_NAME=healthcare
# MONGO_VITALS_COLLECTION=vitals
# ============================================================

MONGO_URI = os.getenv("MONGO_URI", "").strip()
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "healthcare").strip()
MONGO_VITALS_COLLECTION = os.getenv(
    "MONGO_VITALS_COLLECTION",
    "vitals",
).strip()

_mongo_client: Optional[pymongo.MongoClient] = None
_vitals_collection = None
_mongo_lock = threading.Lock()


def get_vitals_collection():
    """
    Lazily create/reuse the MongoDB connection.

    Lazy connection is safer for serverless/cold-start deployments
    than forcing MongoDB connection during module import.
    """
    global _mongo_client, _vitals_collection

    if not MONGO_URI:
        return None

    if _vitals_collection is not None:
        return _vitals_collection

    with _mongo_lock:
        if _vitals_collection is not None:
            return _vitals_collection

        try:
            _mongo_client = pymongo.MongoClient(
                MONGO_URI,
                serverSelectionTimeoutMS=3000,
                connectTimeoutMS=3000,
                socketTimeoutMS=3000,
                maxPoolSize=5,
                minPoolSize=0,
                retryWrites=True,
            )

            _mongo_client.admin.command("ping")

            db = _mongo_client[MONGO_DB_NAME]
            _vitals_collection = db[MONGO_VITALS_COLLECTION]

            print("MongoDB connected successfully.")
            return _vitals_collection

        except Exception as exc:
            print(f"MongoDB connection unavailable: {exc}")
            _mongo_client = None
            _vitals_collection = None
            return None


# ============================================================
# REQUEST MODELS
# ============================================================

class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User's health-related message.",
    )


class SymptomAnalysisRequest(BaseModel):
    symptoms: list[str] = Field(
        ...,
        min_length=1,
        max_length=20,
        description="List of symptoms.",
    )


# ============================================================
# HEALTH / ROOT ENDPOINTS
# ============================================================

@app.get("/")
async def root():
    return {
        "status": "ok",
        "service": "AI Health Chatbot API",
        "version": "1.1.0",
    }


@app.get("/health")
async def health():
    collection = get_vitals_collection()

    return {
        "status": "ok",
        "service": "AI Health Chatbot API",
        "model_file": MODEL_PATH.exists(),
        "mongodb": "connected" if collection is not None else (
            "not configured" if not MONGO_URI else "unavailable"
        ),
    }


# ============================================================
# HEALTH KNOWLEDGE BASE
# ============================================================

condition_info = {
    "heart_attack": {
        "symptoms": [
            "chest pain",
            "shortness of breath",
            "sweating",
            "dizziness",
            "jaw pain",
            "left arm pain",
            "nausea",
        ],
        "risk_factors": [
            "high blood pressure",
            "high cholesterol",
            "smoking",
            "diabetes",
            "obesity",
            "family history",
            "stress",
        ],
        "prevention": [
            "regular exercise",
            "healthy diet",
            "quit smoking",
            "limit alcohol",
            "manage stress",
            "regular check-ups",
        ],
        "emergency_signs": [
            "severe or persistent chest pain",
            "pain spreading to the arm, shoulder, back, neck, or jaw",
            "sudden shortness of breath",
            "cold sweat",
            "fainting or severe lightheadedness",
        ],
    },
    "gastritis": {
        "symptoms": [
            "stomach pain",
            "bloating",
            "heartburn",
            "nausea",
            "vomiting",
            "loss of appetite",
            "feeling full quickly",
        ],
        "risk_factors": [
            "H. pylori infection",
            "regular NSAID use",
            "excessive alcohol",
            "stress",
            "autoimmune disorders",
            "bile reflux",
        ],
        "prevention": [
            "avoid irritating foods",
            "limit alcohol",
            "eat smaller meals",
            "manage stress",
            "avoid unnecessary NSAID use",
            "seek treatment for H. pylori when diagnosed",
        ],
        "diet_recommendations": [
            "avoid foods that trigger your symptoms",
            "limit acidic or spicy foods if they worsen symptoms",
            "limit caffeine if it worsens symptoms",
            "stay hydrated",
            "eat regular, smaller meals",
        ],
        "treatment": [
            "acid-reducing medicines may be used when appropriate",
            "antacids may provide symptom relief",
            "H. pylori requires clinician-directed treatment",
            "avoid identified trigger foods",
            "avoid unnecessary NSAID use",
            "seek medical evaluation for persistent symptoms",
        ],
    },
}


# ============================================================
# TEXT HELPERS
# ============================================================

def normalize_text(value: str) -> str:
    """Normalize whitespace and case for matching."""
    value = value or ""
    value = re.sub(r"\s+", " ", value)
    return value.strip().lower()


def get_suggested_response(message: str):
    """Return predefined responses for common chatbot suggestions."""
    message = normalize_text(message)

    suggested_responses = {
        "i have chest pain": (
            "Chest pain can have many causes, including heart, lung, "
            "digestive, or muscle-related problems. Severe, new, or "
            "persistent chest pain, especially with shortness of breath, "
            "sweating, fainting, or pain spreading to the arm or jaw, "
            "needs urgent medical evaluation."
        ),
        "feeling dizzy": (
            "Dizziness can have several causes, including dehydration, "
            "inner-ear problems, blood-pressure changes, medication "
            "effects, or other conditions. Seek urgent medical care if "
            "dizziness is severe or occurs with fainting, chest pain, "
            "severe headache, weakness, or difficulty speaking."
        ),
        "stomach hurts": (
            "Stomach pain can result from indigestion, gastritis, infection, "
            "ulcers, or other conditions. The location, severity, duration, "
            "and associated symptoms are important. Severe or worsening pain, "
            "persistent vomiting, blood in vomit or stool, fainting, or a "
            "rigid abdomen requires prompt medical evaluation."
        ),
        "shortness of breath": (
            "Shortness of breath can have respiratory, heart-related, "
            "anxiety-related, or other causes. Sudden or severe breathing "
            "difficulty, especially with chest pain, blue lips, fainting, "
            "or confusion, requires emergency medical attention."
        ),
        "how to treat gastritis?": (
            "Gastritis treatment depends on its cause. A clinician may "
            "recommend acid-reducing treatment or other medicines when "
            "appropriate. Avoiding personal triggers and unnecessary NSAID "
            "use may help. Persistent or severe symptoms should be evaluated "
            "by a healthcare professional."
        ),
    }

    return suggested_responses.get(message)


def get_condition_answer(message: str):
    """
    Answer basic condition-information questions from the local
    knowledge base. This is informational and is not a diagnosis.
    """
    message = normalize_text(message)

    heart_attack_patterns = [
        r"\bheart attack\b",
        r"\bcardiac arrest\b",
        r"\bheart pain\b",
        r"\bheart condition\b",
    ]

    gastritis_patterns = [
        r"\bgastritis\b",
        r"\bstomach inflammation\b",
        r"\bstomach pain\b",
        r"\bacid reflux\b",
        r"\bindigestion\b",
    ]

    condition = None

    if any(re.search(pattern, message) for pattern in heart_attack_patterns):
        condition = "heart_attack"
    elif any(re.search(pattern, message) for pattern in gastritis_patterns):
        condition = "gastritis"

    if not condition:
        return None

    info = condition_info[condition]
    readable_name = condition.replace("_", " ")

    if re.search(r"\bsymptom|sign|feel|experiencing\b", message):
        return (
            f"Common symptoms associated with {readable_name} include: "
            + ", ".join(info["symptoms"])
            + ". This information cannot confirm a diagnosis."
        )

    if re.search(r"\bcause|risk factor|reason\b", message):
        return (
            f"Risk factors associated with {readable_name} include: "
            + ", ".join(info["risk_factors"])
            + "."
        )

    if re.search(r"\bprevent|avoid|stop\b", message):
        return (
            f"General prevention measures associated with {readable_name} include: "
            + ", ".join(info["prevention"])
            + "."
        )

    if (
        condition == "gastritis"
        and re.search(r"\btreat|cure|heal|therapy|medication\b", message)
    ):
        return (
            "Gastritis treatment depends on the underlying cause. General "
            "options may include: "
            + ", ".join(info["treatment"])
            + ". A clinician should determine the appropriate treatment."
        )

    if (
        condition == "heart_attack"
        and re.search(r"\bemergency|urgent|serious\b", message)
    ):
        return (
            "Possible heart-attack emergency signs include: "
            + ", ".join(info["emergency_signs"])
            + ". If these symptoms are happening now, seek emergency medical care."
        )

    if (
        condition == "gastritis"
        and re.search(r"\bdiet|eat|food\b", message)
    ):
        return (
            "General dietary considerations for gastritis include: "
            + ", ".join(info["diet_recommendations"])
            + ". Individual triggers vary."
        )

    if condition == "heart_attack":
        return (
            "A heart attack occurs when blood flow to part of the heart "
            "is blocked. It is a medical emergency. Possible symptoms "
            "include chest pressure or pain, shortness of breath, sweating, "
            "nausea, or pain that spreads to the arm, shoulder, back, neck, "
            "or jaw. If these symptoms are happening now, seek emergency care."
        )

    return (
        "Gastritis is inflammation of the stomach lining. Possible symptoms "
        "include stomach discomfort, nausea, bloating, or reduced appetite. "
        "Persistent, severe, or concerning symptoms should be evaluated by "
        "a healthcare professional."
    )


# ============================================================
# SYMPTOM EXTRACTION
# ============================================================

SYMPTOM_ALIASES = {
    "chest pain": [
        "chest pain",
        "chest hurts",
        "pain in my chest",
        "chest discomfort",
    ],
    "shortness of breath": [
        "shortness of breath",
        "breathlessness",
        "difficulty breathing",
        "trouble breathing",
        "can't breathe",
        "cannot breathe",
    ],
    "sweating": [
        "sweating",
        "cold sweat",
        "sweaty",
    ],
    "dizziness": [
        "dizziness",
        "dizzy",
        "feeling dizzy",
    ],
    "jaw pain": [
        "jaw pain",
        "pain in my jaw",
    ],
    "left arm pain": [
        "left arm pain",
        "pain in my left arm",
    ],
    "nausea": [
        "nausea",
        "feeling nauseous",
    ],
    "vomiting": [
        "vomiting",
        "vomit",
    ],
    "stomach pain": [
        "stomach pain",
        "stomach hurts",
        "stomach ache",
        "abdominal pain",
        "belly pain",
    ],
    "bloating": [
        "bloating",
        "bloated",
    ],
    "heartburn": [
        "heartburn",
        "burning in chest after eating",
    ],
    "loss of appetite": [
        "loss of appetite",
        "no appetite",
    ],
    "regurgitation": [
        "regurgitation",
        "food coming back up",
    ],
    "difficulty swallowing": [
        "difficulty swallowing",
        "trouble swallowing",
        "painful swallowing",
    ],
    "racing heart": [
        "racing heart",
        "heart racing",
        "fast heartbeat",
        "palpitations",
    ],
    "coughing": [
        "coughing",
        "cough",
    ],
    "coughing blood": [
        "coughing blood",
        "blood when coughing",
        "coughing up blood",
    ],
}


def extract_symptoms(message: str) -> list[str]:
    """Extract normalized symptoms from free-form chatbot text."""
    text = normalize_text(message)
    found = []

    for symptom, aliases in SYMPTOM_ALIASES.items():
        if any(alias in text for alias in aliases):
            found.append(symptom)

    return found


# ============================================================
# EMERGENCY DETECTION
# ============================================================

EMERGENCY_PATTERNS = [
    r"\bsevere chest pain\b",
    r"\bcrushing chest pain\b",
    r"\bpressure in (my|the) chest\b",
    r"\bcan't breathe\b",
    r"\bcannot breathe\b",
    r"\bsevere shortness of breath\b",
    r"\bcoughing up blood\b",
    r"\bcoughing blood\b",
    r"\bfainted\b",
    r"\bpassed out\b",
    r"\bunconscious\b",
    r"\bblue lips\b",
    r"\bsevere bleeding\b",
]


def emergency_response(message: str) -> Optional[str]:
    """Return an urgent-care message for obvious emergency phrases."""
    text = normalize_text(message)

    if any(re.search(pattern, text) for pattern in EMERGENCY_PATTERNS):
        return (
            "Some symptoms you described can represent a medical emergency. "
            "This chatbot cannot diagnose or rule out an emergency. "
            "If these symptoms are happening now or are severe/worsening, "
            "contact your local emergency service or go to the nearest "
            "emergency department immediately."
        )

    return None


# ============================================================
# MODEL EXECUTION
# ============================================================

MODEL_TIMEOUT_SECONDS = float(
    os.getenv("MODEL_TIMEOUT_SECONDS", "8")
)


def _clean_model_output(output: str) -> str:
    """
    Clean model stdout without assuming a specific model.py format.

    If model.py returns JSON containing prediction/response/result,
    use that field. Otherwise return stdout as text.
    """
    output = (output or "").strip()

    if not output:
        return ""

    # Try complete JSON first.
    try:
        data = json.loads(output)

        if isinstance(data, dict):
            for key in ("prediction", "response", "result", "message"):
                if key in data and data[key] is not None:
                    return str(data[key]).strip()

            return json.dumps(data, ensure_ascii=False)

        if isinstance(data, str):
            return data.strip()

    except json.JSONDecodeError:
        pass

    return output


def run_model(symptoms: list[str]) -> str:
    """
    Execute model.py using the same Python environment.

    model.py is expected to accept one JSON argument, for example:
        python model.py '["chest pain", "dizziness"]'

    A timeout prevents a stuck model from hanging the serverless request.
    """
    if not MODEL_PATH.is_file():
        raise FileNotFoundError(
            f"model.py was not found at: {MODEL_PATH}"
        )

    payload = json.dumps(symptoms, ensure_ascii=False)

    command = [
        sys.executable,
        str(MODEL_PATH),
        payload,
    ]

    print(f"Running model: {MODEL_PATH.name}")

    try:
        completed = subprocess.run(
            command,
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=MODEL_TIMEOUT_SECONDS,
            check=False,
        )

    except subprocess.TimeoutExpired as exc:
        print(f"Model timed out after {MODEL_TIMEOUT_SECONDS} seconds.")
        raise RuntimeError(
            "The AI prediction service timed out."
        ) from exc

    except Exception as exc:
        print(f"Could not start model.py: {exc}")
        raise RuntimeError(
            "The AI prediction engine could not be started."
        ) from exc

    stdout = (completed.stdout or "").strip()
    stderr = (completed.stderr or "").strip()

    if stderr:
        # Keep server logs useful without exposing them to the browser.
        print(f"model.py stderr: {stderr[-4000:]}")

    if completed.returncode != 0:
        print(f"model.py exit code: {completed.returncode}")
        raise RuntimeError(
            f"model.py exited with code {completed.returncode}"
        )

    prediction = _clean_model_output(stdout)

    if not prediction:
        raise RuntimeError("model.py returned an empty prediction.")

    print(f"Model prediction generated successfully.")
    return prediction


# ============================================================
# VITALS
# ============================================================

def get_latest_vitals() -> dict:
    """
    Read the latest vitals if MongoDB is available.
    Returns safe defaults when MongoDB is unavailable.
    """
    defaults = {
        "bp": 120,
        "pulse": 75,
        "sugar": 100,
    }

    collection = get_vitals_collection()

    if collection is None:
        return defaults

    try:
        vitals = collection.find_one(
            {},
            sort=[("_id", -1)],
        ) or {}

        return {
            "bp": vitals.get("bp", defaults["bp"]),
            "pulse": vitals.get("pulse", defaults["pulse"]),
            "sugar": vitals.get("sugar", defaults["sugar"]),
        }

    except Exception as exc:
        print(f"Could not fetch latest vitals: {exc}")
        return defaults


def number_value(value, default: float) -> float:
    """Convert a numeric-looking value safely."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ============================================================
# CHAT ENDPOINT
# ============================================================

@app.post("/api/chat/analyze")
async def analyze_chat(request: ChatRequest):
    message = request.message.strip()

    # 1. Emergency check first.
    urgent = emergency_response(message)

    if urgent:
        return {
            "response": urgent,
            "urgent": True,
        }

    # 2. Common predefined responses.
    suggested_response = get_suggested_response(message)

    if suggested_response:
        return {
            "response": suggested_response,
            "urgent": False,
        }

    # 3. Condition information.
    condition_answer = get_condition_answer(message)

    if condition_answer:
        return {
            "response": condition_answer,
            "urgent": False,
        }

    # 4. Extract symptoms.
    symptoms = extract_symptoms(message)

    if not symptoms:
        return {
            "response": (
                "Please describe your symptoms in more detail. "
                "For example: chest pain, dizziness, stomach pain, "
                "shortness of breath, nausea, or vomiting."
            ),
            "urgent": False,
        }

    # 5. Optional vitals.
    vitals = get_latest_vitals()

    bp = number_value(vitals.get("bp"), 120)
    pulse = number_value(vitals.get("pulse"), 75)
    sugar = number_value(vitals.get("sugar"), 100)

    # 6. AI/model prediction.
    try:
        prediction = run_model(symptoms)

    except Exception as exc:
        print(f"Chat model error: {exc}")

        return {
            "response": (
                "I could not run the AI prediction engine right now. "
                "Please try again in a moment."
            ),
            "urgent": False,
            "prediction_available": False,
        }

    # 7. Add a cautious vitals note.
    vitals_note = ""

    if bp > 140 or pulse > 100:
        vitals_note = (
            " Your latest stored vitals also show an elevated value. "
            "Please discuss abnormal readings with a healthcare professional."
        )

    return {
        "response": (
            f"Based on the symptoms you entered "
            f"({', '.join(symptoms)}), the system suggests: {prediction}"
            f"{vitals_note}"
        ),
        "prediction": prediction,
        "symptoms": symptoms,
        "vitals": {
            "bp": bp,
            "pulse": pulse,
            "sugar": sugar,
        },
        "urgent": False,
        "prediction_available": True,
    }


# ============================================================
# STRUCTURED SYMPTOM ANALYSIS
# ============================================================

@app.post("/api/novelty/analyze")
async def analyze_symptoms(request: SymptomAnalysisRequest):
    symptoms = [
        normalize_text(symptom)
        for symptom in request.symptoms
        if str(symptom).strip()
    ]

    # Remove duplicates while preserving order.
    symptoms = list(dict.fromkeys(symptoms))

    if not symptoms:
        return {
            "prediction": "Please provide at least one valid symptom.",
            "prediction_available": False,
        }

    # Emergency keywords in structured input.
    combined = " ".join(symptoms)
    urgent = emergency_response(combined)

    if urgent:
        return {
            "prediction": urgent,
            "urgent": True,
            "prediction_available": False,
        }

    try:
        prediction = run_model(symptoms)

    except Exception as exc:
        print(f"Structured model error: {exc}")

        return {
            "prediction": (
                "The AI prediction engine could not be executed right now."
            ),
            "prediction_available": False,
        }

    return {
        "prediction": prediction,
        "symptoms": symptoms,
        "urgent": False,
        "prediction_available": True,
    }


# ============================================================
# LOCAL DEVELOPMENT
# ============================================================
#
# Run from this directory:
#
#   uvicorn main:app --reload --port 8000
#
# Vercel imports `app` automatically.
#
# Do NOT add app.run() for FastAPI.
# ============================================================
