import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("POSTGRES_VM_HOST"),
    database=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password = os.getenv("POSTGRES_PASSWORD")
)

cursor = conn.cursor()
cursor.execute("SELECT * FROM users;")
rows = cursor.fetchall()

for row in rows:
    print(row)

cursor.close()
conn.close()