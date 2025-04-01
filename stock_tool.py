import psycopg2
import os
from dotenv import load_dotenv

import auth   #imports the functionality for user login and sign up 

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("POSTGRES_VM_HOST"),
    database=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password = os.getenv("POSTGRES_PASSWORD")
)

cursor = conn.cursor()

# cursor.execute("SELECT * FROM users;")
# rows = cursor.fetchall()

# for row in rows:
#     print(row)

while True:
    print("\n1. Signup")
    print("2. Login")
    print("3. Exit")
    
    choice = input("Choose an option: ")
    
    if choice == "1":
        auth.signup(conn, cursor)
    elif choice == "2":
        auth.login(conn, cursor)
    elif choice == "3":
        break
    else:
        print("❌ Invalid option, try again.")




cursor.close()
conn.close()