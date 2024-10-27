from flask import Flask, render_template, request, redirect, url_for, jsonify
import pandas as pd
import os
import time
from threading import Lock
from flask_compress import Compress

app = Flask(__name__)
Compress(app)  # Enable compression for faster load times

# File lock to prevent race conditions
lock = Lock()

# CSV file path, configurable via environment variable
CSV_FILE = os.getenv("CSV_FILE", os.path.join(os.path.dirname(__file__), 'database.csv'))

# Global variables to cache the data
data_cache = []
data_last_updated = None

# Cache expiry time (in seconds)
CACHE_EXPIRY_TIME = 60 * 5  # 5 minutes

def load_data():
    """Load the CSV file data into memory using Pandas, with caching."""
    global data_cache, data_last_updated
    # Check if data is still fresh
    if data_last_updated and (time.time() - data_last_updated) < CACHE_EXPIRY_TIME:
        return  # Data is still fresh

    with lock:
        try:
            # Load data with Pandas
            df = pd.read_csv(CSV_FILE)
            data_cache = df.to_dict(orient='records')
            data_last_updated = time.time()  # Update last updated time
        except Exception as e:
            data_cache = []
            print(f"Error loading data: {e}")

def format_averages(data):
    """Format the averages to one decimal place."""
    for entry in data:
        for key in ['gmat_average', 'gre_average', 'experience_average', 'gpa_average', 'toefl_average', 'ielts_average']:
            if entry.get(key) is not None:
                entry[key] = f"{float(entry[key]):.1f}"
    return data

@app.route('/')
def index():
    """Displays the courses and related data."""
    load_data()  # Ensure data is loaded
    if not data_cache:
        return "No data available", 404

    # Format averages for display
    formatted_data = format_averages(data_cache)
    courses = {entry['course'] for entry in formatted_data}
    if not courses:
        return "No courses found", 404

    # Pass only the default course data to the frontend
    default_course = next(iter(courses))
    filtered_data = [entry for entry in formatted_data if entry['course'] == default_course]

    return render_template('index.html', courses=courses, default_course=default_course, records=filtered_data)

@app.route('/get_universities/<course>', methods=['GET'])
def get_universities(course):
    """Return university data for a selected course."""
    normalized_course = course.strip().lower()
    filtered_data = [entry for entry in data_cache if entry['course'].strip().lower() == normalized_course]

    if not filtered_data:
        return jsonify({"error": f"No data found for the selected course: {course}"}), 404

    # Format averages for display
    filtered_data = format_averages(filtered_data)

    return jsonify(filtered_data)

@app.route('/get_courses/<university>', methods=['GET'])
def get_courses(university):
    """Return courses for the selected university."""
    courses = {entry['course'] for entry in data_cache if entry['university'] == university}
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

            for entry in data_cache:
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

            save_data()  # Save data after the update
            return redirect(url_for('index'))
        except Exception as e:
            print(f"Error updating data: {e}")
            return "Error updating data", 500

    universities = {entry['university'] for entry in data_cache}
    return render_template('update.html', universities=list(universities))

def save_data():
    """Save the cached data back to the CSV file."""
    with lock:
        try:
            df = pd.DataFrame(data_cache)
            df.to_csv(CSV_FILE, index=False)
        except Exception as e:
            print(f"Error saving data: {e}")

# Load data once on startup
load_data()

if __name__ == '__main__':
    app.run(debug=os.getenv("DEBUG", "False") == "True")
