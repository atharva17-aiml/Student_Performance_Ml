import joblib
import os
import logging

logging.basicConfig(level=logging.INFO)

# ---------------- PATH CONFIG ----------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "..", "model", "model.pkl")

# ---------------- LOAD MODEL ----------------

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Model not found at {MODEL_PATH}")

try:
    model = joblib.load(MODEL_PATH)
    logging.info(f"Model loaded successfully from {MODEL_PATH}")

except Exception as e:
    logging.error(f"Failed to load model: {e}")
    raise


# ---------------- PREDICTION FUNCTION ----------------

def predict_student(features):
    """
    Predict student final score.

    Args:
        features (list[int]): 
            [studytime, failures, absences, health, G1, G2]

    Returns:
        float: predicted score
    """

    if not isinstance(features, list):
        raise ValueError("Features must be a list")

    if len(features) != 6:
        raise ValueError("Features list must contain 6 values")

    try:
        prediction = model.predict([features])[0]
        return float(prediction)

    except Exception as e:
        logging.error(f"Prediction failed: {e}")
        raise