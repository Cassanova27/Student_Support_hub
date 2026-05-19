from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, datetime, timedelta

app = Flask(__name__)
app.secret_key = "student_support_secret_key"

def get_db_connection():
    conn = sqlite3.connect("wellbeing.db")
    conn.row_factory = sqlite3.Row
    return conn

# --- Points calculation ---
def calculate_points(mood, sleep, workload, academic, score):
    points = 10  

    if mood == "happy":
        points += 5
    elif mood == "okay":
        points += 3

    if sleep == "Restful":
        points += 5
    elif sleep == "Okay- managed but not grey":
        points += 3

    if workload == "low":
        points += 3

    if academic == "low":
        points += 3

    if score >= 20:
        points += 10
    elif score >= 12:
        points += 5

    return points

# --- Update streak and total points ---
def update_stats(user_id, points_earned):
    conn = get_db_connection()
    today = str(date.today())
    yesterday = str((datetime.today() - timedelta(days=1)).date())

    stats = conn.execute(
        "SELECT * FROM user_stats WHERE user_id = ?", (user_id,)
    ).fetchone()

    if not stats:
        # First ever check-in for this user
        conn.execute("""
            INSERT INTO user_stats (user_id, total_points, current_streak, last_checkin_date)
            VALUES (?, ?, 1, ?)
        """, (user_id, points_earned, today))
    else:
        last_date = stats["last_checkin_date"]
        streak = stats["current_streak"]

        if last_date == yesterday:
            streak += 1
            points_earned += 5  # streak bonus
        elif last_date != today:
            streak = 1  # streak broken

        conn.execute("""
            UPDATE user_stats
            SET total_points = total_points + ?,
                current_streak = ?,
                last_checkin_date = ?
            WHERE user_id = ?
        """, (points_earned, streak, today, user_id))

    conn.commit()
    conn.close()
    return points_earned

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        try:
            conn.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (username, email, hashed_password)
            )
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            conn.close()
            return "Username or email already exists."

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))
        error = "Invalid email or password"

    return render_template("login.html", error=error)

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    # Get points and streak
    stats = conn.execute(
        "SELECT * FROM user_stats WHERE user_id = ?", (session["user_id"],)
    ).fetchone()

    # Get 5 most recent check-ins
    recent_checkins = conn.execute(
        "SELECT * FROM checkins WHERE user_id = ? ORDER BY date DESC LIMIT 5",
        (session["user_id"],)
    ).fetchall()

    conn.close()

    return render_template("dashboard.html",
        username=session["username"],
        stats=stats,
        recent_checkins=recent_checkins
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/checkin")
def checkin():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("checkin.html")

@app.route("/recommendations", methods=["POST"])
def recommendations():
    mood = request.form.get("mood")
    academic = request.form.get("academic")
    workload = request.form.get("workload")
    social = request.form.get("social")
    financial = request.form.get("financial")
    sleep = request.form.get("sleep")
    rating = request.form.get("rating")

    score = 0
    if mood == "happy": score += 5
    elif mood == "okay": score += 3
    elif mood == "tired": score += 2
    else: score += 1

    if academic == "low": score += 5
    elif academic == "medium": score += 3
    else: score += 1

    if workload == "low": score += 5
    elif workload == "medium": score += 3
    else: score += 1

    if sleep == "restful": score += 5
    elif sleep == "Okay - managed but not great": score += 3
    else: score += 1

    score += int(rating or 0)

    if score >= 20:
        message = "Your wellbeing looks positive today."
        tip = "Keep maintaining your healthy habits and regular check-ins."
    elif score >= 12:
        message = "You may be experiencing some pressure today."
        tip = "Try taking a short break, planning your tasks, or doing something relaxing."
    else:
        message = "It seems like you may be feeling overwhelmed today."
        tip = "Consider reaching out to someone you trust or using university wellbeing support."

    # Calculate and save points
    points_earned = calculate_points(mood, sleep, workload, academic, score)
    points_earned = update_stats(session["user_id"], points_earned)

    conn = get_db_connection()
    conn.execute("""
        INSERT INTO checkins 
        (user_id, mood, academic, workload, social, financial, sleep, rating, score, points_earned)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (session["user_id"], mood, academic, workload, social, financial,
          sleep, rating, score, points_earned))
    conn.commit()
    conn.close()

    survey_avg_score = 15
    user_percentile = round((score / 30) * 100)

    return render_template("recommendations.html",
        message=message,
        tip=tip,
        score=score,
        points_earned=points_earned,
        survey_avg_score=survey_avg_score,
        user_percentile=user_percentile
    )
@app.route("/resources")
def resources():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("resources.html") 

@app.route("/view-checkins")
def view_checkins():
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_db_connection()
    checkins = conn.execute(
        "SELECT * FROM checkins WHERE user_id = ? ORDER BY date DESC",
        (session["user_id"],)
    ).fetchall()
    conn.close()
    return render_template("view_checkins.html", checkins=checkins)

@app.route("/journal", methods=["GET", "POST"])
def journal():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    if request.method == "POST":
        entry = request.form.get("entry")
        if entry:
            conn.execute(
                "INSERT INTO journals (user_id, entry) VALUES (?, ?)",
                (session["user_id"], entry)
            )
            conn.commit()

    entries = conn.execute(
        "SELECT * FROM journals WHERE user_id = ? ORDER BY date DESC",
        (session["user_id"],)
    ).fetchall()
    conn.close()

    return render_template("journal.html", entries=entries)


if __name__ == "__main__":
    app.run(debug=True)

