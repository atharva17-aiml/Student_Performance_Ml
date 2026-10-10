from database import get_connection
import logging

logging.basicConfig(level=logging.INFO)


# ---------------- PERFORMANCE LABEL ----------------

def get_prediction_label(score):

    if score < 8:
        return "At Risk"
    elif score < 12:
        return "Needs Improvement"
    elif score < 15:
        return "Average"
    elif score < 18:
        return "Good"
    else:
        return "Excellent"


# ---------------- SAVE PREDICTION ----------------

def save_prediction(user_id, values, prediction):

    conn = None

    try:
        logging.info(f"Saving prediction for user: {user_id}")

        prediction = round(float(prediction), 2)

        prediction_label = get_prediction_label(prediction)
        model_version = "v1.0"

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO predictions
            (
                user_id,
                studytime,
                failures,
                absences,
                health,
                G1,
                G2,
                predicted_score,
                prediction_label,
                model_version
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            user_id,
            *values,
            prediction,
            prediction_label,
            model_version
        ))

        conn.commit()

        logging.info(
            f"Prediction saved: score={prediction}, "
            f"label={prediction_label}, "
            f"model={model_version}"
        )

    except Exception as e:
        logging.error(f"Error saving prediction: {e}")
        raise

    finally:
        if conn and conn.is_connected():
            conn.close()


# ---------------- USER DASHBOARD STATS ----------------

def get_user_stats(user_id):

    conn = None

    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        cur.execute(
            "SELECT COUNT(*) AS total FROM predictions WHERE user_id=%s",
            (user_id,)
        )
        total_predictions = cur.fetchone()["total"]

        cur.execute(
            "SELECT AVG(predicted_score) AS avg_score "
            "FROM predictions WHERE user_id=%s",
            (user_id,)
        )
        avg_score = cur.fetchone()["avg_score"]

        cur.execute("""
            SELECT predicted_score
            FROM predictions
            WHERE user_id=%s
            ORDER BY created_at DESC
            LIMIT 1
        """, (user_id,))

        latest = cur.fetchone()

        return {
            "total_predictions": total_predictions,
            "avg_score": round(avg_score, 2) if avg_score else 0,
            "latest_score": latest["predicted_score"] if latest else None
        }

    except Exception as e:
        logging.error(f"Error fetching user stats: {e}")

        return {
            "total_predictions": 0,
            "avg_score": 0,
            "latest_score": None
        }

    finally:
        if conn and conn.is_connected():
            conn.close()


# ---------------- USER ROLE (ADMIN / USER) ----------------

def get_user_role(user_id):

    conn = None

    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        cur.execute(
            "SELECT role FROM users WHERE id=%s",
            (user_id,)
        )

        row = cur.fetchone()

        return row["role"] if row else None

    except Exception as e:
        logging.error(f"Error fetching user role: {e}")
        return None

    finally:
        if conn and conn.is_connected():
            conn.close()