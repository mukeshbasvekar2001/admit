from flask import Flask, render_template, request, redirect, url_for, jsonify
import pandas as pd

app = Flask(__name__)

# Path to your CSV file
CSV_FILE = 'database.csv'

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
    default_course = courses[0]  # Select the first course as default (you can customize this)

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
    data = pd.read_csv(CSV_FILE)
    courses = data[data['university'] == university]['course'].unique().tolist()
    return jsonify(courses)

@app.route('/update', methods=['GET', 'POST'])
def update():
    if request.method == 'POST':
        university = request.form['university']
        course = request.form['course']
        gmat_score = request.form.get('gmat', type=float)
        gre_score = request.form.get('gre', type=float)
        experience_years = request.form['experience']
        gpa = request.form['gpa']
        selection_status = request.form['selection_status']

        # Read the current data
        data = pd.read_csv(CSV_FILE)

        # Find the row to update
        row = data[(data['university'] == university) & (data['course'] == course)]
        if not row.empty:
            # Update GMAT
            gmat_avg = row['gmat_average'].values[0] if pd.notnull(row['gmat_average'].values[0]) else 0
            gmat_count = row['gmat_count'].values[0] if pd.notnull(row['gmat_count'].values[0]) else 0

            if gmat_score is not None:
                new_gmat_count = gmat_count + 1
                new_gmat_avg = (gmat_avg * gmat_count + gmat_score) / new_gmat_count
            else:
                new_gmat_count = gmat_count
                new_gmat_avg = gmat_avg

            # Update GRE
            gre_avg = row['gre_average'].values[0] if pd.notnull(row['gre_average'].values[0]) else 0
            gre_count = row['gre_count'].values[0] if pd.notnull(row['gre_count'].values[0]) else 0

            if gre_score is not None:
                new_gre_count = gre_count + 1
                new_gre_avg = (gre_avg * gre_count + gre_score) / new_gre_count
            else:
                new_gre_count = gre_count
                new_gre_avg = gre_avg

            # Update Experience
            exp_avg = row['experience_average'].values[0] if pd.notnull(row['experience_average'].values[0]) else 0
            exp_count = row['experience_count'].values[0] if pd.notnull(row['experience_count'].values[0]) else 0

            new_exp_count = exp_count + 1
            new_exp_avg = (exp_avg * exp_count + float(experience_years)) / new_exp_count

            # Update GPA
            gpa_avg = row['gpa_average'].values[0] if pd.notnull(row['gpa_average'].values[0]) else 0
            gpa_count = row['gpa_count'].values[0] if pd.notnull(row['gpa_count'].values[0]) else 0

            new_gpa_count = gpa_count + 1
            new_gpa_avg = (gpa_avg * gpa_count + float(gpa)) / new_gpa_count

            # Update the DataFrame
            data.loc[(data['university'] == university) & (data['course'] == course), [
                'gmat_average', 'gmat_count', 'gre_average', 'gre_count',
                'experience_average', 'experience_count', 'gpa_average', 'gpa_count'
            ]] = [new_gmat_avg, new_gmat_count, new_gre_avg, new_gre_count, new_exp_avg, new_exp_count, new_gpa_avg, new_gpa_count]

            # Save the updated DataFrame back to CSV
            data.to_csv(CSV_FILE, index=False)

        return redirect(url_for('index'))

    data = pd.read_csv(CSV_FILE)
    universities = data['university'].unique()
    return render_template('update.html', universities=universities)

if __name__ == '__main__':
    app.run(debug=True)
