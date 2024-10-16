from flask import Flask, render_template, request, redirect, url_for, jsonify
import pandas as pd
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
            return pd.read_csv(CSV_FILE)
        except Exception as e:
            logger.error(f"Error loading CSV file: {e}")
            return pd.DataFrame()

def save_data(data):
    """Save the DataFrame back to the CSV file in a thread-safe manner."""
    with lock:
        try:
            logger.info("Saving data to CSV")
            data.to_csv(CSV_FILE, index=False)
        except Exception as e:
            logger.error(f"Error saving CSV file: {e}")

@app.route('/')
def index():
    """Displays the courses and related data."""
    data = load_data()
    if data.empty:
        return "No data available", 404

    courses = data['course'].unique()  # Get unique courses for selection
    if len(courses) == 0:
        return "No courses found", 404

    default_course = courses[0]  # Select the first course as default

    # Filter the data for the default course
    filtered_data = data[data['course'] == default_course].to_dict(orient='records')

    return render_template('index.html', courses=courses, default_course=default_course, records=filtered_data)

@app.route('/get_universities/<course>', methods=['GET'])
def get_universities(course):
    """Return university data for a selected course."""
    data = load_data()  # Load the CSV data
    logger.info(f"Received request for course: {course}")

    # Normalize course names
    normalized_course = course.strip().lower()
    filtered_data = data[data['course'].str.strip().str.lower() == normalized_course]

    if filtered_data.empty:
        logger.warning(f"No data found for course: {normalized_course}")
        return jsonify({"error": f"No data found for the selected course: {course}"}), 404

    records = filtered_data.to_dict(orient='records')
    return jsonify(records)

@app.route('/get_courses/<university>', methods=['GET'])
def get_courses(university):
    """Return courses for the selected university."""
    data = load_data()
    courses = data[data['university'] == university]['course'].unique().tolist()
    return jsonify(courses)

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

            # Load the CSV data
            data = load_data()

            # Find the row that matches the university and course
            row_index = data[(data['university'] == university) & (data['course'] == course)].index

            if not row_index.empty:
                row_index = row_index[0]  # Get the first matching row index

                # GMAT Updates
                gmat_avg = data.loc[row_index, 'gmat_average'] if pd.notnull(data.loc[row_index, 'gmat_average']) else 0
                gmat_count = data.loc[row_index, 'gmat_count'] if pd.notnull(data.loc[row_index, 'gmat_count']) else 0
                if gmat_score is not None:
                    gmat_count += 1
                    gmat_avg = (gmat_avg * (gmat_count - 1) + gmat_score) / gmat_count

                # GRE Updates
                gre_avg = data.loc[row_index, 'gre_average'] if pd.notnull(data.loc[row_index, 'gre_average']) else 0
                gre_count = data.loc[row_index, 'gre_count'] if pd.notnull(data.loc[row_index, 'gre_count']) else 0
                if gre_score is not None:
                    gre_count += 1
                    gre_avg = (gre_avg * (gre_count - 1) + gre_score) / gre_count

                # Experience Updates
                exp_avg = data.loc[row_index, 'experience_average'] if pd.notnull(data.loc[row_index, 'experience_average']) else 0
                exp_count = data.loc[row_index, 'experience_count'] if pd.notnull(data.loc[row_index, 'experience_count']) else 0
                exp_count += 1
                exp_avg = (exp_avg * (exp_count - 1) + experience_years) / exp_count

                # GPA Updates
                gpa_avg = data.loc[row_index, 'gpa_average'] if pd.notnull(data.loc[row_index, 'gpa_average']) else 0
                gpa_count = data.loc[row_index, 'gpa_count'] if pd.notnull(data.loc[row_index, 'gpa_count']) else 0
                gpa_count += 1
                gpa_avg = (gpa_avg * (gpa_count - 1) + gpa) / gpa_count

                # TOEFL Updates
                toefl_avg = data.loc[row_index, 'toefl_average'] if pd.notnull(data.loc[row_index, 'toefl_average']) else 0
                toefl_count = data.loc[row_index, 'toefl_count'] if pd.notnull(data.loc[row_index, 'toefl_count']) else 0
                if toefl_score is not None:
                    toefl_count += 1
                    toefl_avg = (toefl_avg * (toefl_count - 1) + toefl_score) / toefl_count

                # IELTS Updates
                ielts_avg = data.loc[row_index, 'ielts_average'] if pd.notnull(data.loc[row_index, 'ielts_average']) else 0
                ielts_count = data.loc[row_index, 'ielts_count'] if pd.notnull(data.loc[row_index, 'ielts_count']) else 0
                if ielts_score is not None:
                    ielts_count += 1
                    ielts_avg = (ielts_avg * (ielts_count - 1) + ielts_score) / ielts_count

                # Update the values in the DataFrame
                data.loc[row_index, [
                    'gmat_average', 'gmat_count', 'gre_average', 'gre_count',
                    'experience_average', 'experience_count', 'gpa_average', 'gpa_count',
                    'toefl_average', 'toefl_count', 'ielts_average', 'ielts_count'
                ]] = [
                    gmat_avg, gmat_count, gre_avg, gre_count, exp_avg, exp_count,
                    gpa_avg, gpa_count, toefl_avg, toefl_count, ielts_avg, ielts_count
                ]

                # Save the updated data
                save_data(data)

            return redirect(url_for('index'))
        except Exception as e:
            logger.error(f"Error updating data: {e}")
            return "Error updating data", 500

    # Get the available universities for the form
    data = load_data()
    universities = data['university'].unique()
    return render_template('update.html', universities=universities)

if __name__ == '__main__':
    app.run(debug=os.getenv("DEBUG", "False") == "True")
