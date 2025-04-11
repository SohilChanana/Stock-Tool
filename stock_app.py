import auth
from db import conn, cursor
from time import sleep
import portfolio_overview 
import stock_list_overview  
import public_stock_list_overview  
import stocks              
import friends_module       
from ansi_format import style_menu_option, style_input_prompt, style_error, style_success, style_label, style_info

def main_menu():
    """
    Main menu function that handles user authentication and displays the main menu options.
    """
    while True:
        if auth.current_user["username"]:
            print(style_label("\nPlease choose an option:"))
            print(style_menu_option("1. 📁 View Portfolios"))
            print(style_menu_option("2. 📝 View Stock Lists"))
            print(style_menu_option("3. 🌐 View Public Stock Lists"))
            print(style_menu_option("4. 🗓️  Add Daily Stock Data"))
            print(style_menu_option("5. 🤝 Friends Menu"))
            print(style_menu_option("6. 🔓 Logout"))
            print(style_menu_option("7. ❌ Close Application"))
            choice = input(style_input_prompt("Choose an option: "))
            
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
                print(style_error("❌ Invalid option, try again."))
                sleep(1)
        else:
            print(style_info("\n📈 Welcome to the Stock Tool!"))
            print(style_label("Please choose an option:"))
            print(style_menu_option("1. 🆕 Signup"))
            print(style_menu_option("2. 🔐 Login"))
            print(style_menu_option("3. ❌ Close Application"))
            choice = input(style_input_prompt("Choose an option: "))
            
            if choice == "1":
                auth.signup(conn, cursor)
            elif choice == "2":
                auth.login(conn, cursor)
            elif choice == "3":
                break
            else:
                print(style_error("❌ Invalid option, try again."))
                sleep(1)

if __name__ == "__main__":
    try:
        main_menu()
    finally:
        cursor.close()
        conn.close()
        print(style_info("⛔ Application closed.\n"))
        sleep(1)
