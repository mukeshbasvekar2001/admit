from flask import Flask, render_template, request, redirect, url_for
import pandas as pd

app = Flask(__name__)

# Path to your CSV file
CSV_FILE = 'database.csv'

@app.route('/')
def index():
    data = pd.read_csv(CSV_FILE)
    records = data.to_dict(orient='records')
    return render_template('index.html', records=records)

@app.route('/update', methods=['GET', 'POST'])
def update():
    if request.method == 'POST':
        university = request.form['university']
        course = request.form['course']
        
        # Convert GMAT and GRE scores to integers
        gmat_score = int(request.form['gmat'])
        gre_score = int(request.form['gre'])
        
        # Convert Experience and GPA to float
        experience_years = float(request.form['experience'])
        gpa = float(request.form['gpa'])

        # Read the current data
        data = pd.read_csv(CSV_FILE)

        # Find the row to update
        row = data[(data['university'] == university) & (data['course'] == course)]
        if not row.empty:
            # Update GMAT
            gmat_avg = row['gmat_average'].values[0]
            gmat_count = row['gmat_count'].values[0]

            new_gmat_count = gmat_count + 1
            new_gmat_avg = (gmat_avg * gmat_count + gmat_score) / new_gmat_count

            # Update GRE
            gre_avg = row['gre_average'].values[0]
            gre_count = row['gre_count'].values[0]

            new_gre_count = gre_count + 1
            new_gre_avg = (gre_avg * gre_count + gre_score) / new_gre_count

            # Update Experience
            exp_avg = row['experience_average'].values[0]
            exp_count = row['experience_count'].values[0]

            new_exp_count = exp_count + 1
            new_exp_avg = (exp_avg * exp_count + experience_years) / new_exp_count

            # Update GPA
            gpa_avg = row['gpa_average'].values[0]
            gpa_count = row['gpa_count'].values[0]

            new_gpa_count = gpa_count + 1
            new_gpa_avg = (gpa_avg * gpa_count + gpa) / new_gpa_count

            # Update the DataFrame
            data.loc[(data['university'] == university) & (data['course'] == course), 
                      ['gmat_average', 'gmat_count', 'gre_average', 'gre_count', 
                       'experience_average', 'experience_count', 'gpa_average', 'gpa_count']] = [
                          new_gmat_avg, new_gmat_count, new_gre_avg, new_gre_count, 
                          new_exp_avg, new_exp_count, new_gpa_avg, new_gpa_count]

            # Save the updated DataFrame back to CSV
            data.to_csv(CSV_FILE, index=False)

        return redirect(url_for('index'))

    # GET request to display the form
    data = pd.read_csv(CSV_FILE)
    universities = data['university'].unique()
    courses = data['course'].unique()
    return render_template('update.html', universities=universities, courses=courses)

if __name__ == '__main__':
    app.run(debug=True)
