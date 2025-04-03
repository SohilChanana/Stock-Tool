import auth
from db import conn, cursor
from time import sleep
import portfolio_list_view  # Import the portfolio functionality
import stocks     # Import the stocks functionality

def main_menu():
    while True:
        if auth.current_user["username"]:
            print("\nPlease choose an option:")
            print("1. 📁 View Portfolios")
            print("2. 🗓️  Add Daily Stock Data")
            print("3. 🔓 Logout")
            print("4. ❌ Close Application")
            choice = input("Choose an option: ")
            
            if choice == "1":
                portfolio_list_view.portfolio_menu()
            elif choice == "2":
                stocks.add_daily_stock_data()
            elif choice == "3":
                auth.logout()
            elif choice == "4":
                break
            else:
                print("❌ Invalid option, try again.")
                sleep(1)
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
        sleep(1)
