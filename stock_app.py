import auth
from db import conn, cursor
from time import sleep
import portfolio_overview  # Existing portfolio functionality
import stock_list_overview  # Existing personal/ shared stock list functionality
import public_stock_list_overview  # NEW: public stock lists functionality
import stocks               # Existing stock functionality
import friends_module       # Existing friends functionality

def main_menu():
    while True:
        if auth.current_user["username"]:
            print("\nPlease choose an option:")
            print("1. 📁 View Portfolios")
            print("2. 📝 View Stock Lists")
            print("3. 🌐 View Public Stock Lists")
            print("4. 🗓️  Add Daily Stock Data")
            print("5. 🤝 Friends Menu")
            print("6. 🔓 Logout")
            print("7. ❌ Close Application")
            choice = input("Choose an option: ")
            
            if choice == "1":
                portfolio_overview.portfolio_overview_menu()
            elif choice == "2":
                stock_list_overview.stock_list_menu_view()
            elif choice == "3":
                public_stock_list_overview.public_stock_list_menu_view()
            elif choice == "4":
                stocks.add_daily_stock_data()
            elif choice == "5":
                friends_module.friends_menu(auth.current_user["username"])
            elif choice == "6":
                auth.logout()
            elif choice == "7":
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
