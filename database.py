import pandas as pd
import sqlite3

# Read the CSV file into a DataFrame
df = pd.read_csv('database.csv')

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('database.db')

# Write the DataFrame to a SQLite table
df.to_sql('university_data', conn, if_exists='replace', index=False)

# Close the database connection
conn.close()

print("Database 'database.db' created successfully with table 'university_data'.")
