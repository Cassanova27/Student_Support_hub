from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash


app = Flask(__name__)
app.secret_key = "student_support_secret_key"

def get_db_connection():
    conn = sqlite3.connect("wellbeing.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def home():
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
            return "Account created successfully!"

        except sqlite3.IntegrityError:
            conn.close()
            return "Username or email already exists."

    return render_template("signup.html")

@app.route("/checkin")
def checkin():
    return render_template("checkin.html")

@app.route("/recommendations", methods=["POST"])
def recommendations():
    mood = request.form.get("mood")
    academic = request.form.get("academic")
    workload = request.form.get("workload")
    social = request.form.get("social")
    financial = request.form.get("financial")
    activity = request.form.get("activity")
    rating = request.form.get("rating")

    score = 0

    if mood == "happy":
        score += 5
    elif mood == "okay":
        score += 3
    elif mood == "tired":
        score += 2
    else:
        score += 1

    if academic == "low":
        score += 5
    elif academic == "medium":
        score += 3
    else:
        score += 1

    if workload == "low":
        score += 5
    elif workload == "medium":
        score += 3
    else:
        score += 1

    if activity == "high":
        score += 5
    elif activity == "medium":
        score += 3
    else:
        score += 1

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

    conn = get_db_connection()
    conn.execute("""
        INSERT INTO checkins 
        (user_id, mood, academic, workload, social, financial, activity, rating, score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (1, mood, academic, workload, social, financial, activity, rating, score))
    conn.commit()
    conn.close()

    return render_template(
        "recommendations.html",
        message=message,
        tip=tip,
        score=score
    )

@app.route("/view-checkins")
def view_checkins():
    conn = get_db_connection()
    checkins = conn.execute("SELECT * FROM checkins").fetchall()
    conn.close()

    return render_template("view_checkins.html", checkins=checkins)

if __name__ == "__main__":
    app.run(debug=True)