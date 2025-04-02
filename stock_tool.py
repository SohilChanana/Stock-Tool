import auth
from db import conn, cursor
import time

def main_menu():
    while True:
        
        if auth.current_user["username"]:
            print(f"👋 Welcome, {auth.current_user['username']}")
            print("Please choose an option:")
            print("1. 🔓 Logout")
            print("2. ❌ Exit")
            choice = input("Choose an option: ")
            
            if choice == "1":
                auth.logout()
            elif choice == "2":
                break
            else:
                print("❌ Invalid option, try again.")
        else:
            print("\n📈 Welcome to the Stock Tool!")
            print("Please choose an option:")
            print("1. 🆕 Signup")
            print("2. 🔐 Login")
            print("3. ❌ Exit")
            choice = input("Choose an option: ")
            
            if choice == "1":
                auth.signup(conn, cursor)
            elif choice == "2":
                auth.login(conn, cursor)
            elif choice == "3":
                break
            else:
                print("❌ Invalid option, try again.")

if __name__ == "__main__":
    try:
        main_menu()
    finally:
        cursor.close()
        conn.close()
        print("⛔ Application closed.")
        time.sleep(1)