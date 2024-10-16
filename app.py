from flask import Flask, render_template, request, redirect, url_for, jsonify
import pandas as pd
import os

app = Flask(__name__)

CSV_FILE = os.path.join(os.path.dirname(__file__), 'database.csv')

def load_data():
    """Load the CSV file data."""
    try:
        return pd.read_csv(CSV_FILE)
    except Exception as e:
        print(f"Error loading CSV file: {e}")
        return pd.DataFrame()

@app.route('/')
def index():
    """Displays the courses and the related data."""
    data = load_data()
    courses = data['course'].unique()  # Get unique courses for selection
    default_course = courses[0]  # Select the first course as default

    # Filter the data for the default course
    filtered_data = data[data['course'] == default_course].to_dict(orient='records')

    return render_template('index.html', courses=courses, default_course=default_course, records=filtered_data)

@app.route('/get_universities/<course>', methods=['GET'])
def get_universities(course):
    """Return university data for a selected course."""
    data = load_data()
    filtered_data = data[data['course'] == course]  # Filter data based on selected course

    if filtered_data.empty:
        return jsonify({"error": "No data found for the selected course"}), 404

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
        university = request.form['university']
        course = request.form['course']
        gmat_score = request.form.get('gmat', type=float)
        gre_score = request.form.get('gre', type=float)
        experience_years = request.form['experience']
        gpa = request.form['gpa']
        toefl_score = request.form.get('toefl', type=float)
        ielts_score = request.form.get('ielts', type=float)

        # Load the CSV data
        data = pd.read_csv(CSV_FILE)

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
            exp_avg = (exp_avg * (exp_count - 1) + float(experience_years)) / exp_count

            # GPA Updates
            gpa_avg = data.loc[row_index, 'gpa_average'] if pd.notnull(data.loc[row_index, 'gpa_average']) else 0
            gpa_count = data.loc[row_index, 'gpa_count'] if pd.notnull(data.loc[row_index, 'gpa_count']) else 0
            gpa_count += 1
            gpa_avg = (gpa_avg * (gpa_count - 1) + float(gpa)) / gpa_count

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

            # Save the updated DataFrame back to the CSV
            data.to_csv(CSV_FILE, index=False)

        return redirect(url_for('index'))

    # Get the available universities for the form
    data = pd.read_csv(CSV_FILE)
    universities = data['university'].unique()
    return render_template('update.html', universities=universities)

if __name__ == '__main__':
    app.run(debug=True)
