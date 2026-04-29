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
    mood = request.form.get('mood')
    academic = request.form.get('academic')
    workload = request.form.get('workload')
    social = request.form.get('social')
    financial = request.form.get('financial')
    activity = request.form.get('activity')
    rating = request.form.get('rating')

    if mood in ["sad", "angry"] or academic == "high" or workload == "high":
        message = "It seems like you may be feeling overwhelmed today."
        tip = "Try taking a short break, doing a breathing exercise, and reaching out for support if needed."

    elif activity == "low" or mood == "tired" or rating in ["1", "2"]:
        message = "You may be experiencing low energy or tiredness today."
        tip = "Focus on rest, hydration, and giving yourself time to recharge."

    elif financial == "yes" or social == "yes":
        message = "It looks like external pressures may be affecting your wellbeing."
        tip = "Consider speaking to university support services or someone you trust."

    else:
        message = "You seem to be doing fairly well today."
        tip = "Keep maintaining positive habits like rest, balance, and regular check-ins."

    return render_template("recommendations.html", message=message, tip=tip)


if __name__ == "__main__":
    app.run(debug=True)