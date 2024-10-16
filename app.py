from flask import Flask, render_template, request, redirect, url_for, jsonify
import csv
import os
from threading import Lock
import logging
from pathlib import Path

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# File lock to prevent race conditions
lock = Lock()

# CSV file path, configurable via environment variable
CSV_FILE = os.getenv("CSV_FILE", Path(__file__).resolve().parent / 'database.csv')

def load_data():
    """Load the CSV file data in a thread-safe manner."""
    with lock:
        try:
            logger.info("Loading data from CSV")
            with open(CSV_FILE, mode='r') as file:
                reader = csv.DictReader(file)
                return list(reader)
        except Exception as e:
            logger.error(f"Error loading CSV file: {e}")
            return []

def save_data(data):
    """Save the data back to the CSV file in a thread-safe manner."""
    with lock:
        try:
            logger.info("Saving data to CSV")
            with open(CSV_FILE, mode='w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
        except Exception as e:
            logger.error(f"Error saving CSV file: {e}")

@app.route('/')
def index():
    """Displays the courses and related data."""
    data = load_data()
    if not data:
        return "No data available", 404

    courses = {entry['course'] for entry in data}  # Get unique courses
    if not courses:
        return "No courses found", 404

    default_course = next(iter(courses))  # Select the first course as default

    # Filter the data for the default course
    filtered_data = [entry for entry in data if entry['course'] == default_course]

    return render_template('index.html', courses=courses, default_course=default_course, records=filtered_data)

@app.route('/get_universities/<course>', methods=['GET'])
def get_universities(course):
    """Return university data for a selected course."""
    data = load_data()
    logger.info(f"Received request for course: {course}")

    normalized_course = course.strip().lower()
    filtered_data = [entry for entry in data if entry['course'].strip().lower() == normalized_course]

    if not filtered_data:
        logger.warning(f"No data found for course: {normalized_course}")
        return jsonify({"error": f"No data found for the selected course: {course}"}), 404

    return jsonify(filtered_data)

@app.route('/get_courses/<university>', methods=['GET'])
def get_courses(university):
    """Return courses for the selected university."""
    data = load_data()
    courses = {entry['course'] for entry in data if entry['university'] == university}
    return jsonify(list(courses))

@app.route('/update', methods=['GET', 'POST'])
def update():
    """Handles updating the university course data."""
    if request.method == 'POST':
        try:
            university = request.form['university']
            course = request.form['course']
            gmat_score = request.form.get('gmat', type=float)
            gre_score = request.form.get('gre', type=float)
            experience_years = float(request.form['experience'])
            gpa = float(request.form['gpa'])
            toefl_score = request.form.get('toefl', type=float)
            ielts_score = request.form.get('ielts', type=float)

            data = load_data()

            # Find the row that matches the university and course
            for entry in data:
                if entry['university'] == university and entry['course'] == course:
                    # GMAT Updates
                    gmat_count = int(entry.get('gmat_count', 0))
                    gmat_sum = float(entry.get('gmat_average', 0)) * gmat_count
                    if gmat_score is not None:
                        gmat_sum += gmat_score
                        gmat_count += 1
                        entry['gmat_average'] = gmat_sum / gmat_count
                    entry['gmat_count'] = gmat_count

                    # GRE Updates
                    gre_count = int(entry.get('gre_count', 0))
                    gre_sum = float(entry.get('gre_average', 0)) * gre_count
                    if gre_score is not None:
                        gre_sum += gre_score
                        gre_count += 1
                        entry['gre_average'] = gre_sum / gre_count
                    entry['gre_count'] = gre_count

                    # Experience Updates
                    exp_count = int(entry.get('experience_count', 0))
                    exp_sum = float(entry.get('experience_average', 0)) * exp_count
                    exp_count += 1
                    exp_sum += experience_years
                    entry['experience_average'] = exp_sum / exp_count
                    entry['experience_count'] = exp_count

                    # GPA Updates
                    gpa_count = int(entry.get('gpa_count', 0))
                    gpa_sum = float(entry.get('gpa_average', 0)) * gpa_count
                    gpa_count += 1
                    gpa_sum += gpa
                    entry['gpa_average'] = gpa_sum / gpa_count
                    entry['gpa_count'] = gpa_count

                    # TOEFL Updates
                    toefl_count = int(entry.get('toefl_count', 0))
                    toefl_sum = float(entry.get('toefl_average', 0)) * toefl_count
                    if toefl_score is not None:
                        toefl_sum += toefl_score
                        toefl_count += 1
                        entry['toefl_average'] = toefl_sum / toefl_count
                    entry['toefl_count'] = toefl_count

                    # IELTS Updates
                    ielts_count = int(entry.get('ielts_count', 0))
                    ielts_sum = float(entry.get('ielts_average', 0)) * ielts_count
                    if ielts_score is not None:
                        ielts_sum += ielts_score
                        ielts_count += 1
                        entry['ielts_average'] = ielts_sum / ielts_count
                    entry['ielts_count'] = ielts_count

                    break

            # Save the updated data
            save_data(data)

            return redirect(url_for('index'))
        except Exception as e:
            logger.error(f"Error updating data: {e}")
            return "Error updating data", 500

    # Get the available universities for the form
    data = load_data()
    universities = {entry['university'] for entry in data}
    return render_template('update.html', universities=list(universities))

if __name__ == '__main__':
    app.run(debug=os.getenv("DEBUG", "False") == "True")
