from flask import Flask, render_template, request, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from collections import defaultdict
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fitness.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Workout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    activity = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    date = db.Column(db.String(10), nullable=False)
    calories = db.Column(db.Integer, nullable=False)

class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    activity = db.Column(db.String(100), nullable=False, unique=True)
    target_duration = db.Column(db.Integer, nullable=False)

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/activities')
def activities():
    activity_options = [
        {"name": "Running", "icon": "fa-person-running"},
        {"name": "Cycling", "icon": "fa-bicycle"},
        {"name": "Elliptical", "icon": "fa-person-skating"},
        {"name": "Swimming", "icon": "fa-person-swimming"},
        {"name": "Yoga", "icon": "fa-person-praying"},
        {"name": "Weightlifting", "icon": "fa-dumbbell"},
        {"name": "Hiking", "icon": "fa-person-hiking"},
    ]
    return render_template('activities.html', activities=activity_options)

@app.route('/preferences', methods=['GET', 'POST'])
def preferences():
    if request.method == 'POST':
        activity = request.form['activity']
        target = int(request.form['target_duration'])

        goal = Goal.query.filter_by(activity=activity).first()
        if goal:
            goal.target_duration = target
        else:
            db.session.add(Goal(activity=activity, target_duration=target))
        db.session.commit()

    goals = Goal.query.all()
    return render_template('preferences.html', goals=goals)

@app.route('/log')
def log():
    workouts = Workout.query.order_by(Workout.date).all()
    return render_template('log.html', workouts=workouts)

@app.route('/add', methods=['GET', 'POST'])
def add():
    selected_activity = request.args.get('activity', '')
    if request.method == 'POST':
        activity = request.form['activity']
        duration = int(request.form['duration'])
        date = request.form['date']
        calories = int(request.form['calories'])

        new_workout = Workout(activity=activity, duration=duration, date=date, calories=calories)
        db.session.add(new_workout)
        db.session.commit()
        return redirect(url_for('log'))
    return render_template('add.html', selected_activity=selected_activity)

@app.route('/progress')
def progress():
    workouts = Workout.query.all()
    duration_data = defaultdict(int)
    calorie_data = defaultdict(int)

    for w in workouts:
        duration_data[w.date] += w.duration
        calorie_data[w.date] += w.calories

    sorted_dates = sorted(duration_data.keys())
    durations = [duration_data[date] for date in sorted_dates]
    calories = [calorie_data[date] for date in sorted_dates]

    return render_template('progress.html', dates=sorted_dates, durations=durations, calories=calories)

@app.route('/export')
def export():
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Title
    p.setFont("Helvetica-Bold", 16)
    p.drawString(40, height - 50, "Workout Log")
    p.setFont("Helvetica", 10)

    # Column headers
    data = [["Date", "Activity", "Duration (min)", "Calories (kcal)"]]

    # Get all workouts
    workouts = Workout.query.order_by(Workout.date).all()
    for w in workouts:
        data.append([
            w.date.strftime("%Y-%m-%d"),
            w.activity,
            str(w.duration),
            str(w.calories)
        ])

    # Finalize and send
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='workout_log.pdf', mimetype='application/pdf')

@app.route('/delete/<int:workout_id>', methods=['POST'])
def delete_workout(workout_id):
    workout = Workout.query.get_or_404(workout_id)
    db.session.delete(workout)
    db.session.commit()
    return redirect(url_for('log'))

if __name__ == '__main__':
    app.run(debug=True)
