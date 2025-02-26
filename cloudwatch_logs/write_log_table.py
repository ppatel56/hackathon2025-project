import sqlite3
import csv
import pandas as pd
import os
import glob

print('running')

# Define the SQLite database file
db_file = "aws_logs.db"

# Connect to the SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# Drop table
cursor.execute('''
DROP table IF EXISTS cloudwatch_logs
''')

# Create the Glue logs table
cursor.execute('''
CREATE TABLE IF NOT EXISTS cloudwatch_logs (
    timestamp TEXT,
    log_data TEXT,
    job_name TEXT
)
''')

insert_sql  = ''' 
INSERT INTO cloudwatch_logs VALUES (?,?,?) 
'''

for filename in os.listdir(os.getcwd()):
    if filename.split('.')[-1] == 'csv':
        time_stamp = filename.split('.')[0].split('_')[2]
        job_name = filename.split('.')[0].split('_')[0]
        f = open(filename, 'r')
        data = f.read()
        cursor.execute(insert_sql, (time_stamp, data, job_name) )

conn.commit()

res = cursor.execute('''
SELECT timestamp, job_name from cloudwatch_logs
''')
print(res.fetchall())

cursor.close()