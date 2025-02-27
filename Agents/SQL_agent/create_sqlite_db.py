import sqlite3
import csv
import os

# Define the SQLite database file
db_file = os.path.join(os.path.dirname(__file__), '..','aws_logs.db')

# Connect to the SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# Create the Glue logs table
cursor.execute('''
CREATE TABLE IF NOT EXISTS glue_logs (
    timestamp TEXT,
    service TEXT,
    log_level TEXT,
    message TEXT,
    request_id TEXT,
    error_code TEXT,
    details TEXT
)
''')

# Create the Lambda logs table
cursor.execute('''
CREATE TABLE IF NOT EXISTS lambda_logs (
    timestamp TEXT,
    service TEXT,
    log_level TEXT,
    message TEXT,
    request_id TEXT,
    error_code TEXT,
    details TEXT
)
''')

# Function to insert data from a CSV file into a table
def insert_csv_data(csv_file, table_name):
    with open(csv_file, mode='r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header row
        for row in reader:
            cursor.execute(f'''
            INSERT INTO {table_name} (timestamp, service, log_level, message, request_id, error_code, details)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', row)

# Insert data from mock_glue_logs.csv into the glue_logs table
local_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))
insert_csv_data(f"{local_dir}/mock_glue_logs.csv", "glue_logs")

# Insert data from mock_lambda_logs.csv into the lambda_logs table
insert_csv_data(f"{local_dir}/mock_lambda_logs.csv", "lambda_logs")

# Commit the changes and close the connection
conn.commit()
conn.close()

print("SQLite database created and data inserted successfully!")