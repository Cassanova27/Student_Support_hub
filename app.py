from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/checkin")
def checkin():
    return render_template("checkin.html")

@app.route("/recommendations", methods=["POST"])
def recommendations():
    mood = request.form["mood"]
    stress = request.form["stress"]
    sleep = request.form["sleep"]
    energy = request.form["energy"]
    pressure = request.form["pressure"]

    message = ""
    tip = ""

    if mood in ["sad", "angry"] or stress == "high" or pressure == "yes":
        message = "It seems like you may be feeling overwhelmed today."
        tip = "Try taking a short break, doing a breathing exercise, and reaching out for support if needed."
    elif sleep == "poor" or energy == "low" or mood == "tired":
        message = "You may be experiencing low energy or tiredness today."
        tip = "Focus on rest, hydration, and giving yourself time to recharge."
    else:
        message = "You seem to be doing fairly well today."
        tip = "Keep maintaining positive habits like rest, balance, and regular check-ins."

    return render_template("recommendations.html", message=message, tip=tip)

if __name__ == "__main__":
    app.run(debug=True)