import sqlite3
import os

# Connect to the SQLite database
db_file = os.path.join(os.path.dirname(__file__),'..','aws_logs.db')
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# Query 1: Fetch all Glue logs
print("Fetching all Glue logs:")
cursor.execute("SELECT message FROM glue_logs WHERE timestamp LIKE '2023-01-01%' AND message LIKE '%Hackathon-Test-Glue-2%';")
glue_logs = cursor.fetchall()
print(len(glue_logs))

# Close the connection
conn.close()