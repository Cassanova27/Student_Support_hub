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
    points = 1 
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
    error = None
    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        password = request.form.get("password")
        hashed_password = generate_password_hash(password)
       
        if len(password) <8:
            error = "Password must be at least 8 characters."
            return render_template("signup.html", error=error)


        conn = get_db_connection()
        try:
            conn.execute(
                "INSERT INTO users (first_name, last_name, email, password) VALUES (?, ?, ?, ?)",
                (first_name, last_name, email, hashed_password)
            )
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            conn.close()
            error = "An account with this email already exists."

    return render_template("signup.html", error=error)

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
            session["first_name"] = user["first_name"]
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
        first_name=session["first_name"],
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

    tips = []
    low_areas = []

    if mood in ["tired", "low"]:
        low_areas.append(("mood", "😔 Your mood seems low today. Try some self care — a short walk or 5 minutes of deep breathing can help."))
    if academic == "Really Struggling":
        low_areas.append(("academic", "📚 Academic stress is high. Break tasks into smaller steps and tackle one at a time."))
    if workload == "Really Struggling":
        low_areas.append(("workload", "💼 Your workload feels heavy. Prioritise your top 3 tasks and ask for support if needed."))
    if sleep in ["broken", "barely"]:
        low_areas.append(("sleep", "😴 Poor sleep affects everything. Try a consistent bedtime and no screens 30 minutes before bed."))
    if social in ["isolated", "disconnected"]:
        low_areas.append(("social", "👥 You seem disconnected. Try reaching out to one person today — even a quick message helps."))
    if financial == "struggling":
        low_areas.append(("financial", "💰 Financial stress is tough. Check if your university offers hardship funds or speak to a student advisor."))

    if len(low_areas) == 0:
        tips.append("✅ You're doing well across all areas. Keep it up and check in again later⭐!")
    elif len(low_areas) >= 4:
        tips.append("It looks like you're going through a tough time across multiple areas. Be kind to yourself — take things one step at a time and don't hesitate to reach out to university support if things feel overwhelming.")
    else:
        for _, tip in low_areas:
            tips.append(tip)
            
    score = 0
    if mood == "happy": score += 1
    elif mood == "okay": score += 0
    elif mood == "tired": score -= 1
    elif mood == "low": score -= 1

    if academic == "Feeling on top of it": score += 1
    elif academic == "Managing but it's a lot": score += 0
    elif academic == "Really Struggling": score -=1


    if workload == "Feeling on top of it": score += 1
    elif workload == "Managing but it's a lot": score += 0
    elif workload== "Really Struggling": score -=1

    if sleep == "restful": score += 1
    elif sleep == "okay": score += 0
    elif sleep == "broken": score -= 1
    elif sleep == "barely": score -= 1


    if social == "isolated": score -= 1
    elif social == "disconnected": score -= 1
    elif social == "okay": score += 0
    elif social == "connected": score += 1

    if financial == "struggling": score -= 1
    elif financial == "tight": score += 0
    elif financial == "okay": score += 1

    score += int(rating or 0)

    raw_min = -6
    raw_max = 16
    score = max(raw_min, min(raw_max, score))
    score = round((score - raw_min) / (raw_max - raw_min)* 10)

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

    survey_avg_score = 5
    

    return render_template("recommendations.html",
        tips=tips,
        score=score,
        points_earned=points_earned,
        survey_avg_score=survey_avg_score,
      
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

