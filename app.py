from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import os
from threading import Lock
import logging
from pathlib import Path
from flask_compress import Compress

app = Flask(__name__)
Compress(app)  # Enable compression for faster load times

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# File lock to prevent race conditions
lock = Lock()

# JSON file path, configurable via environment variable
JSON_FILE = os.getenv("JSON_FILE", str(Path(__file__).resolve().parent / 'database.json'))
logger.info(f"Using JSON file at: {JSON_FILE}")

# Global variables to cache the data
data_cache = []
data_last_updated = None

def load_data():
    """Load the JSON file data in a thread-safe manner only if cache is empty or outdated."""
    global data_cache, data_last_updated
    with lock:
        if data_cache and data_last_updated == os.path.getmtime(JSON_FILE):
            return data_cache
        try:
            logger.info("Loading data from JSON")
            with open(JSON_FILE, mode='r') as file:
                data_cache = json.load(file)
                data_last_updated = os.path.getmtime(JSON_FILE)
                return data_cache
        except Exception as e:
            logger.error(f"Error loading JSON file: {e}")
            return []

def save_data(data):
    """Save the data back to the JSON file in a thread-safe manner and update cache."""
    global data_cache
    with lock:
        try:
            logger.info("Saving data to JSON")
            with open(JSON_FILE, mode='w') as file:
                json.dump(data, file, indent=4)
            # Update cache after saving data
            data_cache = data
            data_last_updated = os.path.getmtime(JSON_FILE)
        except Exception as e:
            logger.error(f"Error saving JSON file: {e}")

def format_averages(data):
    """Format the averages to two decimal places."""
    for entry in data:
        for key in ['gmat_average', 'gre_average', 'experience_average', 'gpa_average', 'toefl_average', 'ielts_average']:
            if entry.get(key) is not None:
                entry[key] = f"{float(entry[key]):.1f}"
    return data

@app.route('/')
def index():
    """Displays the courses and related data."""
    data = load_data()
    if not data:
        return "No data available", 404

    # Format averages for display
    data = format_averages(data)

    courses = {entry['course'] for entry in data}
    if not courses:
        return "No courses found", 404

    # Pass only the default course data to the frontend
    default_course = next(iter(courses))
    filtered_data = [entry for entry in data if entry['course'] == default_course]

    return render_template('index.html', courses=courses, default_course=default_course, records=filtered_data)

@app.route('/get_universities/<course>', methods=['GET'])
def get_universities(course):
    """Return university data for a selected course."""
    data = load_data()
    normalized_course = course.strip().lower()
    filtered_data = [entry for entry in data if entry['course'].strip().lower() == normalized_course]

    if not filtered_data:
        return jsonify({"error": f"No data found for the selected course: {course}"}), 404

    # Format averages for display
    filtered_data = format_averages(filtered_data)

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
            gmat_score = request.form.get('gmat', type=float) or None
            gre_score = request.form.get('gre', type=float) or None
            experience_years = float(request.form['experience'])
            gpa = float(request.form['gpa'])
            toefl_score = request.form.get('toefl', type=float) or None
            ielts_score = request.form.get('ielts', type=float) or None

            data = load_data()
            logger.info(f"Form submitted with data: {request.form}")

            for entry in data:
                if entry['university'] == university and entry['course'] == course:
                    # Update GMAT
                    gmat_count = int(entry.get('gmat_count', 0))
                    gmat_sum = float(entry.get('gmat_average', 0)) * gmat_count
                    if gmat_score is not None:
                        gmat_sum += gmat_score
                        gmat_count += 1
                        entry['gmat_average'] = gmat_sum / gmat_count
                    entry['gmat_count'] = gmat_count

                    # Update GRE
                    gre_count = int(entry.get('gre_count', 0))
                    gre_sum = float(entry.get('gre_average', 0)) * gre_count
                    if gre_score is not None:
                        gre_sum += gre_score
                        gre_count += 1
                        entry['gre_average'] = gre_sum / gre_count
                    entry['gre_count'] = gre_count

                    # Update Experience
                    exp_count = int(entry.get('experience_count', 0))
                    exp_sum = float(entry.get('experience_average', 0)) * exp_count
                    exp_sum += experience_years
                    exp_count += 1
                    entry['experience_average'] = exp_sum / exp_count
                    entry['experience_count'] = exp_count

                    # Update GPA
                    gpa_count = int(entry.get('gpa_count', 0))
                    gpa_sum = float(entry.get('gpa_average', 0)) * gpa_count
                    gpa_sum += gpa
                    gpa_count += 1
                    entry['gpa_average'] = gpa_sum / gpa_count
                    entry['gpa_count'] = gpa_count

                    # Update TOEFL
                    toefl_count = int(entry.get('toefl_count', 0))
                    toefl_sum = float(entry.get('toefl_average', 0)) * toefl_count
                    if toefl_score is not None:
                        toefl_sum += toefl_score
                        toefl_count += 1
                        entry['toefl_average'] = toefl_sum / toefl_count
                    entry['toefl_count'] = toefl_count

                    # Update IELTS
                    ielts_count = int(entry.get('ielts_count', 0))
                    ielts_sum = float(entry.get('ielts_average', 0)) * ielts_count
                    if ielts_score is not None:
                        ielts_sum += ielts_score
                        ielts_count += 1
                        entry['ielts_average'] = ielts_sum / ielts_count
                    entry['ielts_count'] = ielts_count

                    break

            save_data(data)
            logger.info(f"Updated data successfully for {university} - {course}")
            return redirect(url_for('index'))
        except Exception as e:
            logger.error(f"Error updating data: {e}")
            return "Error updating data", 500

    data = load_data()
    universities = {entry['university'] for entry in data}
    return render_template('update.html', universities=list(universities))

if __name__ == '__main__':
    app.run(debug=os.getenv("DEBUG", "False") == "True")
