from flask import Flask, render_template, request, redirect, url_for, jsonify
import pandas as pd

app = Flask(__name__)

# Path to your CSV file
CSV_FILE = 'database.csv'

@app.route('/')
def index():
    data = pd.read_csv(CSV_FILE)
    records = data.to_dict(orient='records')
    universities = data['university'].unique()
    return render_template('index.html', records=records, universities=universities)

@app.route('/update', methods=['GET', 'POST'])
def update():
    if request.method == 'POST':
        university = request.form['university']
        course = request.form['course']
        selection_status = request.form['selection_status']
        
        # Convert GMAT and GRE scores to integers, default to None if not provided
        gmat_score = request.form['gmat']
        gmat_score = int(gmat_score) if gmat_score else None
        
        gre_score = request.form['gre']
        gre_score = int(gre_score) if gre_score else None
        
        # Convert Experience and GPA to float
        experience_years = float(request.form['experience'])
        gpa = float(request.form['gpa'])

        # Read the current data
        data = pd.read_csv(CSV_FILE)

        # Find the row to update
        row = data[(data['university'] == university) & (data['course'] == course)]
        
        if not row.empty and selection_status == 'Selected':
            new_data = {}

            if gmat_score is not None:
                new_data['gmat_average'] = (row['gmat_average'].values[0] * row['gmat_count'].values[0] + gmat_score) / (row['gmat_count'].values[0] + 1)
                new_data['gmat_count'] = row['gmat_count'].values[0] + 1
            else:
                new_data['gmat_average'] = row['gmat_average'].values[0]
                new_data['gmat_count'] = row['gmat_count'].values[0]

            if gre_score is not None:
                new_data['gre_average'] = (row['gre_average'].values[0] * row['gre_count'].values[0] + gre_score) / (row['gre_count'].values[0] + 1)
                new_data['gre_count'] = row['gre_count'].values[0] + 1
            else:
                new_data['gre_average'] = row['gre_average'].values[0]
                new_data['gre_count'] = row['gre_count'].values[0]

            new_data['experience_average'] = (row['experience_average'].values[0] * row['experience_count'].values[0] + experience_years) / (row['experience_count'].values[0] + 1)
            new_data['experience_count'] = row['experience_count'].values[0] + 1
            
            new_data['gpa_average'] = (row['gpa_average'].values[0] * row['gpa_count'].values[0] + gpa) / (row['gpa_count'].values[0] + 1)
            new_data['gpa_count'] = row['gpa_count'].values[0] + 1

            # Update the DataFrame
            data.loc[(data['university'] == university) & (data['course'] == course), list(new_data.keys())] = list(new_data.values())

            # Save the updated DataFrame back to CSV
            data.to_csv(CSV_FILE, index=False)

        return redirect(url_for('index'))

    # GET request to display the form
    data = pd.read_csv(CSV_FILE)
    universities = data['university'].unique()
    return render_template('update.html', universities=universities)

@app.route('/get_courses/<university>', methods=['GET'])
def get_courses(university):
    data = pd.read_csv(CSV_FILE)
    courses = data[data['university'] == university]['course'].tolist()
    return jsonify(courses)

if __name__ == '__main__':
    app.run(debug=True)
