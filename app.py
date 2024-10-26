from flask import Flask, render_template, request, redirect, url_for, jsonify
from threading import Lock
from pathlib import Path
import sqlite3
import logging
from flask_compress import Compress
import os

app = Flask(__name__)
Compress(app)  # Enable compression for faster load times

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SQLite database path
DATABASE = str(Path(__file__).resolve().parent / 'database.db')

# Lock for thread safety
lock = Lock()

def get_db_connection():
    """Create a new database connection."""
    conn = sqlite3.connect(DATABASE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def format_averages(data):
    """Format the averages to two decimal places for display."""
    for entry in data:
        for key in ['gmat_average', 'gre_average', 'experience_average', 'gpa_average', 'toefl_average', 'ielts_average']:
            if entry.get(key) is not None:
                entry[key] = f"{float(entry[key]):.1f}"
    return data

@app.route('/')
def index():
    """Display a default course with related data."""
    with get_db_connection() as conn:
        courses = conn.execute('SELECT DISTINCT course FROM university_data').fetchall()
        if not courses:
            return "No courses found", 404

        # Convert to a set of courses
        courses = {row['course'] for row in courses}
        default_course = next(iter(courses))

        # Load data for only the default course
        filtered_data = conn.execute(
            'SELECT * FROM university_data WHERE course = ?', (default_course,)
        ).fetchall()
        filtered_data = [dict(row) for row in filtered_data]

    # Format averages for display
    filtered_data = format_averages(filtered_data)

    return render_template('index.html', courses=courses, default_course=default_course, records=filtered_data)

@app.route('/get_universities/<course>', methods=['GET'])
def get_universities(course):
    """Return university data for a selected course only."""
    with get_db_connection() as conn:
        normalized_course = course.strip().lower()
        filtered_data = conn.execute(
            'SELECT * FROM university_data WHERE LOWER(course) = ?', (normalized_course,)
        ).fetchall()
        filtered_data = [dict(row) for row in filtered_data]

    if not filtered_data:
        return jsonify({"error": f"No data found for the selected course: {course}"}), 404

    # Format averages for display
    filtered_data = format_averages(filtered_data)

    return jsonify(filtered_data)

@app.route('/get_courses/<university>', methods=['GET'])
def get_courses(university):
    """Return courses for a selected university."""
    with get_db_connection() as conn:
        courses = conn.execute(
            'SELECT DISTINCT course FROM university_data WHERE university = ?', (university,)
        ).fetchall()
        courses = [row['course'] for row in courses]

    return jsonify(courses)

@app.route('/update', methods=['GET', 'POST'])
def update():
    """Handle updating the university course data."""
    if request.method == 'POST':
        try:
            university = request.form['university']
            course = request.form['course']
            gmat_score = request.form.get('gmat', type=float) or None
            gre_score = request.form.get('gre', type=float) or None
            experience_years = float(request.form['experience'])
            gpa = float(request.form['gpa'])
            toefl_score = request.form.get('toefl', type=float) or None
            ielts_score = request.form.get('ielts', type=float) or None

            with get_db_connection() as conn:
                # Get current data for the university and course
                entry = conn.execute(
                    'SELECT * FROM university_data WHERE university = ? AND course = ?',
                    (university, course)
                ).fetchone()

                if entry:
                    # Calculate and update averages
                    def update_average(score, count, avg):
                        """Helper to calculate new average."""
                        if score is not None:
                            count += 1
                            avg = ((avg * (count - 1)) + score) / count
                        return count, avg

                    gmat_count, gmat_avg = update_average(gmat_score, entry['gmat_count'], entry['gmat_average'])
                    gre_count, gre_avg = update_average(gre_score, entry['gre_count'], entry['gre_average'])
                    exp_count, exp_avg = update_average(experience_years, entry['experience_count'], entry['experience_average'])
                    gpa_count, gpa_avg = update_average(gpa, entry['gpa_count'], entry['gpa_average'])
                    toefl_count, toefl_avg = update_average(toefl_score, entry['toefl_count'], entry['toefl_average'])
                    ielts_count, ielts_avg = update_average(ielts_score, entry['ielts_count'], entry['ielts_average'])

                    # Update the database
                    conn.execute('''
                        UPDATE university_data SET
                            gmat_average = ?, gmat_count = ?,
                            gre_average = ?, gre_count = ?,
                            experience_average = ?, experience_count = ?,
                            gpa_average = ?, gpa_count = ?,
                            toefl_average = ?, toefl_count = ?,
                            ielts_average = ?, ielts_count = ?
                        WHERE university = ? AND course = ?
                    ''', (gmat_avg, gmat_count, gre_avg, gre_count, exp_avg, exp_count,
                          gpa_avg, gpa_count, toefl_avg, toefl_count, ielts_avg, ielts_count,
                          university, course))
                    conn.commit()

            logger.info(f"Updated data successfully for {university} - {course}")
            return redirect(url_for('index'))
        except Exception as e:
            logger.error(f"Error updating data: {e}")
            return "Error updating data", 500

    # Load list of universities
    with get_db_connection() as conn:
        universities = conn.execute('SELECT DISTINCT university FROM university_data').fetchall()
        universities = [row['university'] for row in universities]

    return render_template('update.html', universities=universities)

if __name__ == '__main__':
    app.run(debug=os.getenv("DEBUG", "False") == "True", threaded=True)
