import auth
from db import conn, cursor
import portfolio  # Import the portfolio functionality
import time

def main_menu():
    while True:
        if auth.current_user["username"]:
            print("\nPlease choose an option:")
            print("1. 🔓 Logout")
            print("2. 📁 View Portfolios")
            print("3. ❌ Close Application")
            choice = input("Choose an option: ")
            
            if choice == "1":
                auth.logout()
            elif choice == "2":
                portfolio.portfolio_menu()  # Call the portfolio functionality
            elif choice == "3":
                break
            else:
                print("❌ Invalid option, try again.")
        else:
            print("\n📈 Welcome to the Stock Tool!")
            print("Please choose an option:")
            print("1. 🆕 Signup")
            print("2. 🔐 Login")
            print("3. ❌ Close Application")
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
        print("⛔ Application closed.\n")
        time.sleep(1)
