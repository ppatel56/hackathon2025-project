import sqlite3
import csv
import os

# Define the SQLite database file
db_file = os.path.join(os.path.dirname(__file__),'..','aws_logs.db')

# Connect to the SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# Create the Glue logs table
cursor.execute('''
CREATE TABLE IF NOT EXISTS glue_logs (
    timestamp TEXT,
    jobname TEXT,
    loglevel TEXT,
    message TEXT
)
''')

# Function to insert data from a CSV file into a table
def insert_csv_data(csv_file, table_name):
    with open(csv_file, mode='r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header row
        for row in reader:
            cursor.execute(f'''
            INSERT INTO {table_name} (timestamp,jobname,loglevel,message)
            VALUES (?, ?, ?, ?)
            ''', row)

# Insert data from mock_glue_logs.csv into the glue_logs table
local_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))
# for i in range(1, 5):
#     insert_csv_data(f"{local_dir}/log-events-viewer-result-{i}.csv", "glue_logs")

insert_csv_data(f"{local_dir}/sample_glue_logs.csv", "glue_logs")

# Commit the changes and close the connection
conn.commit()
conn.close()

print("SQLite database created and data inserted successfully!")