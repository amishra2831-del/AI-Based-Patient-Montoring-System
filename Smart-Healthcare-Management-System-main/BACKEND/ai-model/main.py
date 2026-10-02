# main.py
# FastAPI backend for AI Health Chatbot

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from pathlib import Path
import os
import sys
import subprocess
import json
import pymongo
import re


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="AI Health Chatbot API",
    version="1.0.0"
)


# ============================================================
# CORS CONFIGURATION
# ============================================================

# Production frontend + local development
ALLOWED_ORIGINS = [
    "https://health-frontend-rho.vercel.app",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# PATH CONFIGURATION
# ============================================================

# Always find model.py relative to this main.py file.
# This is important when running on Vercel.
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model.py"


# ============================================================
# MONGODB CONNECTION
# ============================================================

# IMPORTANT:
# Add MONGO_URI in the Vercel environment variables.
#
# Example:
# MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/

MONGO_URI = os.getenv("MONGO_URI")

client = None
db = None
vitals_collection = None

if MONGO_URI:
    try:
        client = pymongo.MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000
        )

        # Test connection
        client.admin.command("ping")

        db = client.healthcare
        vitals_collection = db.vitals

        print("MongoDB connected successfully")

    except Exception as e:
        print("MongoDB connection error:", str(e))
        client = None
        db = None
        vitals_collection = None

else:
    print("WARNING: MONGO_URI environment variable is not configured.")


# ============================================================
# REQUEST MODELS
# ============================================================

class ChatRequest(BaseModel):
    message: str


class SymptomAnalysisRequest(BaseModel):
    symptoms: list


# ============================================================
# ROOT / HEALTH CHECK
# ============================================================

@app.get("/")
async def root():
    return {
        "status": "ok",
        "service": "AI Health Chatbot API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "AI Health Chatbot API",
        "mongodb": "connected" if vitals_collection is not None else "not configured"
    }


# ============================================================
# HEALTH CONDITION KNOWLEDGE BASE
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
            "nausea"
        ],

        "risk_factors": [
            "high blood pressure",
            "high cholesterol",
            "smoking",
            "diabetes",
            "obesity",
            "family history",
            "stress"
        ],

        "prevention": [
            "regular exercise",
            "healthy diet",
            "quit smoking",
            "limit alcohol",
            "manage stress",
            "regular check-ups"
        ],

        "emergency_signs": [
            "severe chest pain",
            "pain spreading to arms/jaw",
            "sudden shortness of breath",
            "cold sweat",
            "lightheadedness"
        ]
    },

    "gastritis": {
        "symptoms": [
            "stomach pain",
            "bloating",
            "heartburn",
            "nausea",
            "vomiting",
            "loss of appetite",
            "feeling full quickly"
        ],

        "risk_factors": [
            "h. pylori infection",
            "regular nsaid use",
            "excessive alcohol",
            "stress",
            "autoimmune disorders",
            "bile reflux"
        ],

        "prevention": [
            "avoid irritating foods",
            "limit alcohol",
            "eat smaller meals",
            "manage stress",
            "avoid nsaids",
            "treatment for h. pylori"
        ],

        "diet_recommendations": [
            "avoid spicy foods",
            "limit acidic foods",
            "avoid caffeine",
            "eat high-fiber foods",
            "stay hydrated",
            "eat regularly"
        ],

        "treatment": [
            "proton pump inhibitors",
            "acid reducers",
            "antacids",
            "antibiotics (for H. pylori)",
            "eliminate trigger foods",
            "stress reduction techniques",
            "smaller meals",
            "avoid alcohol"
        ]
    }
}


# ============================================================
# SUGGESTED RESPONSE HANDLER
# ============================================================

def get_suggested_response(message):
    """
    Provide predefined responses for common suggested queries.
    """

    message = message.lower().strip()

    suggested_responses = {

        "i have chest pain":
            "Chest pain can be caused by heart issues (like angina or heart attack), "
            "lung problems, digestive issues, or muscle strain. Seek emergency medical "
            "attention for severe chest pain, especially with shortness of breath or "
            "pain radiating to arm/jaw. Does the pain come and go or is it constant?",

        "feeling dizzy":
            "Dizziness may be caused by inner ear problems, dehydration, blood pressure "
            "issues, or anxiety. For persistent dizziness or if accompanied by severe "
            "headache or vision changes, please seek medical attention. Are you "
            "experiencing any other symptoms with your dizziness?",

        "stomach hurts":
            "Stomach pain could be indigestion, gastritis, food poisoning, or something "
            "more serious like ulcers or appendicitis. The location and timing of your "
            "pain can help determine the cause. Can you describe where exactly the pain "
            "is located?",

        "shortness of breath":
            "Shortness of breath may result from respiratory issues, heart problems, "
            "anxiety, or overexertion. Sudden severe breathing difficulty, especially "
            "with chest pain, could be an emergency requiring immediate medical "
            "attention. Is this a new symptom for you?",

        "how to treat gastritis?":
            "Gastritis treatment includes medications like antacids or acid reducers, "
            "avoiding trigger foods (spicy, acidic), eating smaller meals, and avoiding "
            "alcohol and NSAIDs. For persistent symptoms, please consult with your "
            "healthcare provider for proper diagnosis and treatment plan."
    }

    return suggested_responses.get(message)


# ============================================================
# CONDITION ANSWER HANDLER
# ============================================================

def get_condition_answer(message):
    """
    Extract health condition questions and provide answers
    based on the local knowledge base.
    """

    message = message.lower()

    heart_attack_patterns = [
        r"heart attack",
        r"cardiac arrest",
        r"heart pain",
        r"heart condition"
    ]

    gastritis_patterns = [
        r"gastritis",
        r"stomach inflammation",
        r"stomach pain",
        r"acid reflux",
        r"indigestion"
    ]

    condition = None

    if any(
        re.search(pattern, message)
        for pattern in heart_attack_patterns
    ):
        condition = "heart_attack"

    elif any(
        re.search(pattern, message)
        for pattern in gastritis_patterns
    ):
        condition = "gastritis"

    if not condition:
        return None

    # --------------------------------------------------------
    # Symptoms
    # --------------------------------------------------------

    if re.search(
        r"symptom|sign|feel|experiencing",
        message
    ):
        return (
            f"Common symptoms of {condition.replace('_', ' ')} include: "
            + ", ".join(condition_info[condition]["symptoms"])
        )

    # --------------------------------------------------------
    # Causes / Risk factors
    # --------------------------------------------------------

    elif re.search(
        r"cause|risk factor|reason",
        message
    ):
        return (
            f"Risk factors for {condition.replace('_', ' ')} include: "
            + ", ".join(condition_info[condition]["risk_factors"])
        )

    # --------------------------------------------------------
    # Prevention
    # --------------------------------------------------------

    elif re.search(
        r"prevent|avoid|stop",
        message
    ):
        return (
            f"Prevention measures for {condition.replace('_', ' ')} include: "
            + ", ".join(condition_info[condition]["prevention"])
        )

    # --------------------------------------------------------
    # Gastritis treatment
    # --------------------------------------------------------

    elif (
        re.search(
            r"treat|cure|heal|therapy|medication",
            message
        )
        and condition == "gastritis"
    ):
        return (
            "Treatment options for gastritis include: "
            + ", ".join(condition_info[condition]["treatment"])
        )

    # --------------------------------------------------------
    # Heart attack emergency signs
    # --------------------------------------------------------

    elif (
        condition == "heart_attack"
        and re.search(
            r"emergency|urgent|serious",
            message
        )
    ):
        return (
            "Emergency signs of a heart attack include: "
            + ", ".join(condition_info[condition]["emergency_signs"])
        )

    # --------------------------------------------------------
    # Gastritis diet
    # --------------------------------------------------------

    elif (
        condition == "gastritis"
        and re.search(
            r"diet|eat|food",
            message
        )
    ):
        return (
            "Dietary recommendations for gastritis: "
            + ", ".join(condition_info[condition]["diet_recommendations"])
        )

    # --------------------------------------------------------
    # General heart attack information
    # --------------------------------------------------------

    elif condition == "heart_attack":
        return (
            "A heart attack occurs when blood flow to part of the heart "
            "is blocked, causing damage to heart muscle. It's a medical "
            "emergency requiring immediate attention. Common symptoms "
            "include chest pain, shortness of breath, and pain radiating "
            "to the arm or jaw."
        )

    # --------------------------------------------------------
    # General gastritis information
    # --------------------------------------------------------

    elif condition == "gastritis":
        return (
            "Gastritis is inflammation of the stomach lining, often caused "
            "by infection, excessive alcohol, or regular use of certain "
            "pain relievers. Symptoms include stomach pain, nausea, and "
            "reduced appetite. Most cases can be managed with lifestyle "
            "changes and medication."
        )

    return None


# ============================================================
# RUN MODEL.PY
# ============================================================

def run_model(symptoms):
    """
    Execute model.py using an absolute path.

    This avoids problems caused by Vercel's working directory.
    """

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"model.py not found at: {MODEL_PATH}"
        )

    try:

        process = subprocess.Popen(
            [
                sys.executable,
                str(MODEL_PATH),
                json.dumps(symptoms)
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(BASE_DIR)
        )

        output, error = process.communicate()

        prediction = output.decode(
            "utf-8",
            errors="replace"
        ).strip()

        error_output = error.decode(
            "utf-8",
            errors="replace"
        ).strip()

        if process.returncode != 0:

            print(
                "Model process failed:",
                error_output
            )

            raise RuntimeError(
                error_output or
                f"model.py exited with code {process.returncode}"
            )

        if not prediction:
            raise RuntimeError(
                "model.py returned an empty prediction"
            )

        print(
            "Prediction:",
            prediction
        )

        return prediction

    except Exception as e:

        print(
            "Model execution error:",
            str(e)
        )

        raise


# ============================================================
# CHAT ANALYSIS ENDPOINT
# ============================================================

@app.post("/api/chat/analyze")
async def analyze_chat(request: ChatRequest):

    message = request.message.strip()

    if not message:

        return {
            "response": "Please enter a message."
        }

    # --------------------------------------------------------
    # Suggested responses
    # --------------------------------------------------------

    suggested_response = get_suggested_response(
        message
    )

    if suggested_response:

        return {
            "response": suggested_response
        }

    # --------------------------------------------------------
    # Specific condition questions
    # --------------------------------------------------------

    condition_answer = get_condition_answer(
        message.lower()
    )

    if condition_answer:

        return {
            "response": condition_answer
        }

    # --------------------------------------------------------
    # Extract known symptoms
    # --------------------------------------------------------

    message_lower = message.lower()

    known_symptoms = [
        "chest pain",
        "shortness of breath",
        "sweating",
        "dizziness",
        "jaw pain",
        "left arm pain",
        "nausea",
        "vomiting",
        "stomach pain",
        "bloating",
        "heartburn",
        "loss of appetite",
        "regurgitation",
        "difficulty swallowing",
        "racing heart",
        "coughing",
        "coughing blood"
    ]

    symptoms = [
        symptom
        for symptom in known_symptoms
        if symptom in message_lower
    ]

    # --------------------------------------------------------
    # No known symptoms
    # --------------------------------------------------------

    if not symptoms:

        return {
            "response":
                "Please describe your symptoms in more detail, "
                "or ask a specific question about heart attack "
                "or gastritis."
        }

    # --------------------------------------------------------
    # Fetch latest vitals
    # --------------------------------------------------------

    bp = 120
    pulse = 75
    sugar = 100

    if vitals_collection is not None:

        try:

            vitals = (
                vitals_collection
                .find_one(
                    sort=[("_id", -1)]
                )
                or {}
            )

            bp = vitals.get(
                "bp",
                120
            )

            pulse = vitals.get(
                "pulse",
                75
            )

            sugar = vitals.get(
                "sugar",
                100
            )

        except Exception as e:

            print(
                "Could not fetch vitals:",
                str(e)
            )

    # --------------------------------------------------------
    # Run AI/model prediction
    # --------------------------------------------------------

    try:

        prediction = run_model(
            symptoms
        )

    except Exception as e:

        return {
            "response":
                "The prediction engine could not be executed "
                "at the moment.",
            "error": str(e)
        }

    # --------------------------------------------------------
    # Modify severity based on vitals
    # --------------------------------------------------------

    if "low" in prediction.lower():

        try:

            if bp > 140 or pulse > 100:

                prediction += (
                    "\nNote: Your vitals indicate elevated "
                    "risk. Consider medical advice."
                )

        except Exception:

            pass

    # --------------------------------------------------------
    # Final response
    # --------------------------------------------------------

    return {
        "response":
            f"Based on symptoms ({', '.join(symptoms)}), "
            f"the system suggests: {prediction}"
    }


# ============================================================
# STRUCTURED SYMPTOM ANALYSIS
# ============================================================

@app.post("/api/novelty/analyze")
async def analyze_symptoms(
    request: SymptomAnalysisRequest
):

    # --------------------------------------------------------
    # Validate symptoms
    # --------------------------------------------------------

    if not request.symptoms:

        return {
            "prediction":
                "Please provide at least one symptom."
        }

    symptoms = [
        str(symptom).lower().strip()
        for symptom in request.symptoms
        if str(symptom).strip()
    ]

    if not symptoms:

        return {
            "prediction":
                "Please provide at least one valid symptom."
        }

    # --------------------------------------------------------
    # Run model
    # --------------------------------------------------------

    try:

        prediction = run_model(
            symptoms
        )

    except Exception as e:

        return {
            "prediction":
                "Error analyzing symptoms.",
            "error": str(e)
        }

    return {
        "prediction": prediction
    }


# ============================================================
# LOCAL DEVELOPMENT
# ============================================================

# Vercel handles the server in production.
#
# For local development:
#
# uvicorn main:app --reload --port 8000
#
# Do not use app.run() here.