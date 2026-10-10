from flask import (
    Flask, render_template, request, redirect,
    session, flash, Response
)
from datetime import timedelta, datetime
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
import logging
import random
from services.recommendation_service import generate_recommendations
from services.audit_service import log_action, get_audit_logs

from database import get_connection
from services.ml_service import predict_student
from services.validation import (
    validate_prediction_inputs,
    validate_password
)
from services.db_service import (
    save_prediction,
    get_user_stats,
    get_user_role
)

# ---------------- CONFIG ----------------
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

app.permanent_session_lifetime = timedelta(hours=2)

# Secure session cookies
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Enable only when deploying over HTTPS
app.config["SESSION_COOKIE_SECURE"] = False

logging.basicConfig(level=logging.INFO)

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        f = request.form

        username = f.get("username", "").strip()
        institute = f.get("institute", "").strip()
        roll_no = f.get("roll_no", "").strip()
        birth_date = f.get("birth_date", "").strip()
        password = f.get("password", "")

        # Basic validation
        if not username:
            return render_template(
                "register.html",
                error="Username cannot be empty."
            )

        if not institute:
            return render_template(
                "register.html",
                error="Institute cannot be empty."
            )

        if not roll_no:
            return render_template(
                "register.html",
                error="Roll number cannot be empty."
            )

        if not birth_date:
            return render_template(
                "register.html",
                error="Birth date is required."
            )

        # Password strength validation
        password_valid, password_error = validate_password(password)

        if not password_valid:
            return render_template(
                "register.html",
                error=password_error
            )

        db = None

        try:

            db = get_connection()
            cur = db.cursor()

            cur.execute("""
                INSERT INTO users
                (username, password, institute, roll_no, birth_date)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                username,
                generate_password_hash(password),
                institute,
                roll_no,
                birth_date
            ))

            db.commit()

            # Audit log
            log_action(
                username=username,
                action="USER_REGISTERED",
                description="New student account registered.",
                ip_address=request.remote_addr
            )

            return redirect("/login")

        except Exception as e:

            if db:
                db.rollback()

            logging.error(f"Register error: {e}")

            return render_template(
                "register.html",
                error="Registration failed. Username may already exist."
            )

        finally:

            if db and db.is_connected():
                db.close()

    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        db = None

        try:

            db = get_connection()
            cur = db.cursor(dictionary=True)

            cur.execute(
                "SELECT * FROM users WHERE username=%s",
                (username,)
            )

            user = cur.fetchone()

            if not user or not check_password_hash(
                user["password"],
                password
            ):

                # AUDIT FAILED LOGIN
                log_action(
                    username=username,
                    action="LOGIN_FAILED",
                    description="Failed login attempt.",
                    ip_address=request.remote_addr
                )

                return render_template(
                    "login.html",
                    error="Invalid credentials"
                )

            session.update({
                "user_id": user["id"],
                "username": user["username"],
                "role": user["role"],
                "institute": user["institute"],
                "roll_no": user["roll_no"],
                "birth_date": str(user["birth_date"])
            })

            # AUDIT SUCCESSFUL LOGIN
            log_action(
                user_id=user["id"],
                username=user["username"],
                action="LOGIN_SUCCESS",
                description="User logged in successfully.",
                ip_address=request.remote_addr
            )

            return redirect("/")

        except Exception as e:

            logging.error(
                f"Login error: {e}"
            )

            return render_template(
                "login.html",
                error="Login failed. Please try again."
            )

        finally:

            if db and db.is_connected():
                db.close()

    return render_template("login.html")


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():

    if "user_id" in session:

        log_action(
            user_id=session.get("user_id"),
            username=session.get("username"),
            action="LOGOUT",
            description="User logged out.",
            ip_address=request.remote_addr
        )

    session.clear()

    return redirect("/login")

# ---------------- DASHBOARD ----------------
@app.route("/")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    stats = get_user_stats(session["user_id"])

    total_users = None

    if session.get("role") == "admin":

        db = get_connection()
        cur = db.cursor()

        cur.execute("SELECT COUNT(*) FROM users")
        total_users = cur.fetchone()[0]

        db.close()

    return render_template(
        "index.html",
        total_predictions=stats["total_predictions"],
        avg_score=stats["avg_score"],
        latest_score=stats["latest_score"],
        total_users=total_users,
        profile_username=session["username"],
        profile_institute=session["institute"],
        profile_roll_no=session["roll_no"],
        profile_birth_date=session["birth_date"]
    )


# ---------------- PROFILE ----------------
@app.route("/profile", methods=["GET", "POST"])
def profile():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        institute = request.form["institute"]
        roll_no = request.form["roll_no"]
        birth_date = request.form["birth_date"]

        try:
            db = get_connection()
            cur = db.cursor()

            cur.execute("""
                UPDATE users
                SET institute=%s, roll_no=%s, birth_date=%s
                WHERE id=%s
            """, (institute, roll_no, birth_date, session["user_id"]))

            db.commit()

        except Exception as e:
            logging.error(f"Profile update error: {e}")

        finally:
            db.close()

        session["institute"] = institute
        session["roll_no"] = roll_no
        session["birth_date"] = birth_date

        flash("✅ Profile updated successfully!")

        return redirect("/profile")

    return render_template("profile.html")


# ---------------- PREDICT ----------------
@app.route("/predict", methods=["POST"])
def predict():

    if "user_id" not in session:
        return redirect("/login")

    try:

        values = validate_prediction_inputs(request.form)
        
        prediction = predict_student(values)
        
        log_action(
        user_id=session["user_id"],
        username=session.get("username"),
        action="PREDICTION_CREATED",
        description=f"Student performance prediction generated. Score: {round(prediction, 2)}",
        ip_address=request.remote_addr
        )
        
        studytime, failures, absences, health, G1, G2 = values
        
        recommendations = generate_recommendations(
            studytime=studytime,
            failures=failures,
            absences=absences,
            health=health,
            G1=G1,
            G2=G2,
            predicted_score=prediction
            )
        
        save_prediction(
    session["user_id"],
    values,
    prediction
)

        stats = get_user_stats(session["user_id"])

        total_users = None

        if session.get("role") == "admin":

            db = get_connection()
            cur = db.cursor()

            cur.execute("SELECT COUNT(*) FROM users")
            total_users = cur.fetchone()[0]

            db.close()

        return render_template(
            "index.html",
            total_predictions=stats["total_predictions"],
            avg_score=stats["avg_score"],
            latest_score=stats["latest_score"],
            total_users=total_users,
            profile_username=session["username"],
            profile_institute=session["institute"],
            profile_roll_no=session["roll_no"],
            profile_birth_date=session["birth_date"],
            success_msg=f"✅ Prediction successful! Score: {round(prediction, 2)}"
        )

    except Exception as e:

        logging.error(f"Prediction error: {e}")

        return render_template(
            "index.html",
            success_msg=f"❌ Prediction failed: {e}"
        )


# ---------------- HISTORY ----------------
@app.route("/history")
def history():

    if "user_id" not in session:
        return redirect("/login")

    db = get_connection()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT
            studytime,
            failures,
            absences,
            health,
            G1,
            G2,
            predicted_score,
            prediction_label,
            model_version,
            created_at
        FROM predictions
        WHERE user_id=%s
        ORDER BY created_at DESC
    """, (session["user_id"],))

    rows = cur.fetchall()
    print("HISTORY DATA:")
    print(rows)

    db.close()

    return render_template(
        "history.html",
        rows=rows
    )


# ---------------- ANALYSIS ----------------
@app.route("/analysis")
def analysis():

    if "user_id" not in session:
        return redirect("/login")

    db = get_connection()
    cur = db.cursor()

    cur.execute("""
        SELECT predicted_score FROM predictions
        WHERE user_id=%s ORDER BY id
    """, (session["user_id"],))

    rows = cur.fetchall()

    db.close()

    scores = [float(r[0]) for r in rows]

    labels = list(range(1, len(scores) + 1))

    return render_template("analysis.html", scores=scores, labels=labels)


# ---------------- ADMIN DASHBOARD ----------------
@app.route("/admin")
def admin():

    if "user_id" not in session:
        return redirect("/login")

    user_role = get_user_role(session["user_id"])

    if not user_role or str(user_role).lower() != "admin":
        return "Access Denied", 403

    db = None

    try:

        db = get_connection()
        cur = db.cursor(dictionary=True)

        # =========================================================
        # REGISTERED USERS
        # =========================================================

        cur.execute("""
            SELECT
                id,
                username,
                institute,
                roll_no,
                birth_date,
                role
            FROM users
            ORDER BY id
        """)

        users = cur.fetchall()

        # =========================================================
        # ALL PREDICTIONS
        # =========================================================

        cur.execute("""
            SELECT
                u.username,
                u.institute,
                u.roll_no,
                u.birth_date,
                p.predicted_score,
                p.prediction_label,
                p.model_version,
                p.confidence,
                p.created_at
            FROM predictions p
            JOIN users u
                ON p.user_id = u.id
            ORDER BY p.created_at DESC
        """)

        predictions = cur.fetchall()

        # =========================================================
        # TOTAL USERS
        # =========================================================

        cur.execute("""
            SELECT COUNT(*) AS total_users
            FROM users
        """)

        total_users = cur.fetchone()["total_users"]

        # =========================================================
        # TOTAL PREDICTIONS
        # =========================================================

        cur.execute("""
            SELECT COUNT(*) AS total_predictions
            FROM predictions
        """)

        total_predictions = cur.fetchone()["total_predictions"]

        # =========================================================
        # AVERAGE SCORE
        # =========================================================

        cur.execute("""
            SELECT AVG(predicted_score) AS avg_score
            FROM predictions
        """)

        avg_result = cur.fetchone()

        avg_score = (
            round(float(avg_result["avg_score"]), 2)
            if avg_result["avg_score"] is not None
            else 0
        )

        # =========================================================
        # MODEL VERSION
        # =========================================================

        cur.execute("""
            SELECT model_version
            FROM predictions
            WHERE model_version IS NOT NULL
            ORDER BY created_at DESC
            LIMIT 1
        """)

        model_result = cur.fetchone()

        current_model = (
            model_result["model_version"]
            if model_result
            else "N/A"
        )

        # =========================================================
        # PERFORMANCE DISTRIBUTION
        # =========================================================

        cur.execute("""
            SELECT
                prediction_label,
                COUNT(*) AS total
            FROM predictions
            WHERE prediction_label IS NOT NULL
            GROUP BY prediction_label
            ORDER BY prediction_label
        """)

        performance_distribution = cur.fetchall()

        # =========================================================
        # PREDICTIONS PER DAY
        # =========================================================

        cur.execute("""
            SELECT
                DATE(created_at) AS day,
                COUNT(*) AS total
            FROM predictions
            GROUP BY DATE(created_at)
            ORDER BY DATE(created_at)
        """)

        chart_data = cur.fetchall()

        for item in chart_data:

            if item.get("day"):
                item["day"] = item["day"].strftime("%Y-%m-%d")

        # =========================================================
        # HIGH / LOW PERFORMANCE COUNTS
        # =========================================================

        cur.execute("""
            SELECT COUNT(*) AS total
            FROM predictions
            WHERE prediction_label IN ('Excellent', 'Good')
        """)

        good_predictions = cur.fetchone()["total"]

        cur.execute("""
            SELECT COUNT(*) AS total
            FROM predictions
            WHERE prediction_label IN ('At Risk', 'Needs Improvement')
        """)

        risk_predictions = cur.fetchone()["total"]

        return render_template(
            "admin.html",

            # Existing data
            users=users,
            predictions=predictions,
            chart_data=chart_data,

            # New analytics
            total_users=total_users,
            total_predictions=total_predictions,
            avg_score=avg_score,
            current_model=current_model,
            performance_distribution=performance_distribution,
            good_predictions=good_predictions,
            risk_predictions=risk_predictions
        )

    except Exception as e:

        logging.error(
            f"Admin page error: {e}"
        )

        return f"Admin page error: {e}", 500

    finally:

        if db and db.is_connected():
            db.close()

    # ================= ADMIN ACCESS CHECK =================

    if "user_id" not in session:
        return redirect("/login")

    user_role = get_user_role(session["user_id"])

    if not user_role or str(user_role).lower() != "admin":
        return "Access Denied", 403
    db = None

    try:

        db = get_connection()
        cur = db.cursor(dictionary=True)

        # ==================================================
        # USERS
        # ==================================================

        cur.execute("""
            SELECT
                id,
                username,
                institute,
                roll_no,
                birth_date,
                role
            FROM users
            ORDER BY id
        """)

        users = cur.fetchall()

        # ==================================================
        # ALL PREDICTIONS
        # ==================================================

        cur.execute("""
            SELECT
                u.username,
                u.institute,
                u.roll_no,
                u.birth_date,
                p.predicted_score,
                p.prediction_label,
                p.model_version,
                p.confidence,
                p.created_at
            FROM predictions p
            JOIN users u
                ON p.user_id = u.id
            ORDER BY p.created_at DESC
        """)

        predictions = cur.fetchall()

        # ==================================================
        # PREDICTIONS PER DAY
        # ==================================================

        cur.execute("""
            SELECT
                DATE(created_at) AS day,
                COUNT(*) AS total
            FROM predictions
            GROUP BY DATE(created_at)
            ORDER BY DATE(created_at)
        """)

        chart_data = cur.fetchall()

        # Convert date objects to strings
        # so Chart.js/Jinja can safely serialize them.
        for item in chart_data:
            if item.get("day"):
                item["day"] = item["day"].strftime("%Y-%m-%d")

        return render_template(
            "admin.html",
            users=users,
            predictions=predictions,
            chart_data=chart_data
        )

    except Exception as e:

        logging.error(f"Admin page error: {e}")

        return f"Admin page error: {e}", 500

    finally:

        if db and db.is_connected():
            db.close()


# ---------------- CSV EXPORT ----------------
@app.route("/admin/export-csv")
def export_predictions_csv():

    # Check login
    if "user_id" not in session:
        return redirect("/login")

    # Check admin role from database
    user_role = get_user_role(session["user_id"])

    if not user_role or str(user_role).lower() != "admin":
        return "Access Denied", 403

    db = None

    try:

        # Connect to database
        db = get_connection()

        # Dictionary cursor because we access columns by name
        cur = db.cursor(dictionary=True)

        # Fetch all predictions
        cur.execute("""
            SELECT
                u.username,
                u.institute,
                u.roll_no,
                u.birth_date,
                p.studytime,
                p.failures,
                p.absences,
                p.health,
                p.G1,
                p.G2,
                p.predicted_score,
                p.created_at
            FROM predictions p
            JOIN users u
                ON p.user_id = u.id
            ORDER BY p.created_at DESC
        """)

        rows = cur.fetchall()

    except Exception as e:

        logging.error(
            f"CSV export error: {e}"
        )

        return "Failed to export predictions.", 500

    finally:

        if db and db.is_connected():
            db.close()


    # ============================================================
    # GENERATE CSV
    # ============================================================

    def generate():

        header = [
            "username",
            "institute",
            "roll_no",
            "birth_date",
            "studytime",
            "failures",
            "absences",
            "health",
            "G1",
            "G2",
            "predicted_score",
            "created_at"
        ]

        # CSV header
        yield ",".join(header) + "\n"


        # CSV rows
        for r in rows:

            row = []

            for h in header:

                val = r[h]

                if val is None:
                    val = ""

                # Format datetime
                if isinstance(val, datetime):
                    val = val.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )

                # Remove commas so CSV columns don't break
                val = str(val).replace(",", " ")

                row.append(val)

            yield ",".join(row) + "\n"


    # ============================================================
    # DOWNLOAD CSV
    # ============================================================

    return Response(

        generate(),

        mimetype="text/csv",

        headers={
            "Content-Disposition":
                "attachment; filename=all_predictions.csv"
        }

    )

# ---------------- ADMIN RESET USER PASSWORD ----------------

@app.route("/admin/reset-password/<int:user_id>", methods=["POST"])
def admin_reset_password(user_id):

    # Check login
    if "user_id" not in session:
        return redirect("/login")

    # Check admin role
    user_role = get_user_role(session["user_id"])

    if not user_role or str(user_role).lower() != "admin":
        return "Access Denied", 403

    new_password = request.form.get("new_password", "")

    # Password strength validation
    password_valid, password_error = validate_password(new_password)

    if not password_valid:
        flash(password_error)
        return redirect("/admin")

    db = None

    try:

        db = get_connection()
        cur = db.cursor()

        # Prevent admin from resetting their own password
        if user_id == session["user_id"]:
            flash("You cannot reset your own password from this panel.")
            return redirect("/admin")

        # Check user exists
        cur.execute(
            "SELECT username FROM users WHERE id=%s",
            (user_id,)
        )

        user = cur.fetchone()

        if not user:
            flash("User not found.")
            return redirect("/admin")

        # Hash password
        hashed_password = generate_password_hash(new_password)

        cur.execute("""
            UPDATE users
            SET password=%s
            WHERE id=%s
        """, (
            hashed_password,
            user_id
        ))

        db.commit()

        # Audit log
        log_action(
            user_id=session["user_id"],
            username=session.get("username"),
            action="ADMIN_PASSWORD_RESET",
            description=f"Admin reset password for user: {user[0]}",
            ip_address=request.remote_addr
        )

        flash(f"Password reset successfully for user: {user[0]}")

    except Exception as e:

        if db:
            db.rollback()

        logging.error(f"Admin password reset error: {e}")

        flash("Failed to reset password.")

    finally:

        if db and db.is_connected():
            db.close()

    return redirect("/admin")

# ============================================================
# FORGOT PASSWORD
# ============================================================

@app.route("/forgot", methods=["GET", "POST"])
def forgot():

    if request.method == "GET":
        return render_template("forgot.html")

    username = request.form.get("username", "").strip()

    if not username:
        return render_template(
            "forgot.html",
            error="Please enter your username."
        )

    db = None

    try:
        db = get_connection()
        cur = db.cursor(dictionary=True)

        # Find user
        cur.execute(
            """
            SELECT id, username
            FROM users
            WHERE username=%s
            """,
            (username,)
        )

        user = cur.fetchone()

        if not user:
            return render_template(
                "forgot.html",
                error="Username not found."
            )

        user_id = user["id"]

        # Generate 6-digit OTP
        otp = str(random.randint(100000, 999999))

        # Delete previous OTPs for this user
        cur.execute(
            """
            DELETE FROM password_otp
            WHERE user_id=%s
            """,
            (user_id,)
        )
        cur.execute(
            """
            INSERT INTO password_otp
            (
                user_id,
                email,
                otp,
                expires_at
            )
            VALUES (
                %s,
                %s,
                %s,
                DATE_ADD(NOW(), INTERVAL 10 MINUTE)
            )
            """,
            (
                user_id,
                "",
                otp
            )
        )

        db.commit()

        # Store reset information
        session["reset_user_id"] = user_id
        session["reset_username"] = username

        # Display OTP in Flask terminal
        print()
        print("=" * 60)
        print(f"PASSWORD RESET OTP")
        print(f"Username : {username}")
        print(f"OTP      : {otp}")
        print(f"Expires  : 10 minutes")
        print("=" * 60)
        print()

        return redirect("/verify-otp")

    except Exception as e:

        if db:
            db.rollback()

        logging.error(f"Forgot password error: {e}")
        print(f"FORGOT PASSWORD ERROR: {e}")

        return render_template(
            "forgot.html",
            error="Something went wrong. Please try again."
        )

    finally:

        if db and db.is_connected():
            db.close()

# ============================================================
# VERIFY OTP
# ============================================================

@app.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():

    if "reset_user_id" not in session:
        return redirect("/forgot")

    if request.method == "GET":
        return render_template(
            "verify_otp.html",
            username=session.get("reset_username")
        )

    entered_otp = request.form.get("otp", "").strip()

    if not entered_otp:
        return render_template(
            "verify_otp.html",
            username=session.get("reset_username"),
            error="Please enter the OTP."
        )

    db = None

    try:

        db = get_connection()
        cur = db.cursor(dictionary=True)

        cur.execute(
            """
            SELECT otp, expires_at
            FROM password_otp
            WHERE user_id=%s
            ORDER BY id DESC
            LIMIT 1
            """,
            (session["reset_user_id"],)
        )

        record = cur.fetchone()

        if not record:
            return render_template(
                "verify_otp.html",
                username=session.get("reset_username"),
                error="OTP not found. Please request a new OTP."
            )

        # Check OTP
        if str(record["otp"]) != entered_otp:

            return render_template(
                "verify_otp.html",
                username=session.get("reset_username"),
                error="Invalid OTP."
            )

        # Check expiration
        cur.execute(
            """
            SELECT
                CASE
                    WHEN expires_at >= NOW()
                    THEN 1
                    ELSE 0
                END AS valid
            FROM password_otp
            WHERE user_id=%s
            ORDER BY id DESC
            LIMIT 1
            """,
            (session["reset_user_id"],)
        )

        expiry_check = cur.fetchone()

        if not expiry_check or expiry_check["valid"] != 1:

            return render_template(
                "verify_otp.html",
                username=session.get("reset_username"),
                error="OTP has expired. Please request a new OTP."
            )

        # OTP verified
        session["otp_verified"] = True

        return redirect("/reset-password")

    except Exception as e:

        logging.error(f"OTP verification error: {e}")
        print(f"OTP VERIFICATION ERROR: {e}")

        return render_template(
            "verify_otp.html",
            username=session.get("reset_username"),
            error="Something went wrong."
        )

    finally:

        if db and db.is_connected():
            db.close()

# ============================================================
# RESET PASSWORD
# ============================================================

@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():

    if "reset_user_id" not in session:
        return redirect("/forgot")

    if not session.get("otp_verified"):
        return redirect("/verify-otp")

    if request.method == "GET":
        return render_template("reset_password.html")

    new_password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    # Password strength validation
    password_valid, password_error = validate_password(new_password)

    if not password_valid:
        return render_template(
            "reset_password.html",
            error=password_error
        )

    # Confirm password
    if new_password != confirm_password:
        return render_template(
            "reset_password.html",
            error="Passwords do not match."
        )

    db = None

    try:

        db = get_connection()
        cur = db.cursor()

        hashed_password = generate_password_hash(new_password)

        cur.execute(
            """
            UPDATE users
            SET password=%s
            WHERE id=%s
            """,
            (
                hashed_password,
                session["reset_user_id"]
            )
        )

        # Delete used OTP
        cur.execute(
            """
            DELETE FROM password_otp
            WHERE user_id=%s
            """,
            (session["reset_user_id"],)
        )

        db.commit()

        # Audit log
        log_action(
            user_id=session["reset_user_id"],
            username=session.get("reset_username"),
            action="PASSWORD_RESET",
            description="User password reset successfully using OTP.",
            ip_address=request.remote_addr
        )

        # Clear reset session
        session.pop("reset_user_id", None)
        session.pop("reset_username", None)
        session.pop("otp_verified", None)

        return redirect("/login?reset=success")

    except Exception as e:

        if db:
            db.rollback()

        logging.error(f"Password reset error: {e}")

        return render_template(
            "reset_password.html",
            error="Failed to reset password."
        )

    finally:

        if db and db.is_connected():
            db.close()


# ---------------- ADMIN AUDIT LOGS ----------------
@app.route("/admin/audit-logs")
def admin_audit_logs():

    if "user_id" not in session:
        return redirect("/login")

    user_role = get_user_role(session["user_id"])

    if not user_role or str(user_role).lower() != "admin":
        return "Access Denied", 403

    logs = get_audit_logs()

    return render_template(
        "audit_logs.html",
        logs=logs
    )

# ---------------- RUN ----------------
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )