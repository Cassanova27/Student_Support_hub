from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def handle_login():
    return redirect(url_for('home'))

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/checkin')
def checkin():
    return render_template('checkin.html')

@app.route('/resources')
def resources():
    return render_template('resources.html')

@app.route('/submit', methods=['POST'])
def submit():
    mood = request.form.get('mood')
    stress = request.form.get('stress')
    sleep = request.form.get('sleep')

    print("Mood:", mood)
    print("Stress:", stress)
    print("Sleep:", sleep)

    return render_template('thankyou.html')

if __name__ == '__main__':
    app.run(debug=True)