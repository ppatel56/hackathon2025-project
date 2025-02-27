import sqlite3

# Connect to the SQLite database
db_file = "aws_logs.db"
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# Query 1: Fetch all Glue logs
print("Fetching all Glue logs:")
cursor.execute("SELECT * FROM glue_logs")
glue_logs = cursor.fetchall()
for log in glue_logs:
    print(log)

# Query 2: Fetch all Lambda logs
print("\nFetching all Lambda logs:")
cursor.execute("SELECT * FROM lambda_logs")
lambda_logs = cursor.fetchall()
for log in lambda_logs:
    print(log)

# Query 3: Count logs by service
print("\nCounting logs by service:")
cursor.execute('''
    SELECT service, COUNT(*) as log_count
    FROM (
        SELECT service FROM glue_logs
        UNION ALL
        SELECT service FROM lambda_logs
    )
    GROUP BY service
''')
log_counts = cursor.fetchall()
for service, count in log_counts:
    print(f"{service}: {count} logs")

# Close the connection
conn.close()