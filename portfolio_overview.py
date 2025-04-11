import auth
from db import conn, cursor
import portfolio_menu
from time import sleep
from ansi_format import style_menu_option, style_input_prompt, style_error, style_success, style_label, style_info

def portfolio_overview_menu():
    while True:
        # Display the user's current portfolios and capture them
        portfolios = display_portfolios()
        
        # Present the portfolio functionality menu
        print(style_label("\n📁 Portfolio Menu:"))
        print(style_menu_option("1. 🆕 Create Portfolio"))
        if portfolios:
            print(style_menu_option("2. 🔍 Open Portfolio"))
            print(style_menu_option("3. 🔙 Go Back"))
        else:
            print(style_menu_option("2. 🔙 Go Back"))
            
        choice = input(style_input_prompt("Choose an option: "))
        
        if choice == "1":
            create_portfolio()
        elif choice == "2" and portfolios:
            open_portfolio(portfolios)
        elif (choice == "2" and not portfolios) or (choice == "3" and portfolios):
            break
        else:
            print(style_error("❌ Invalid option, please try again."))
            sleep(1)

def display_portfolios():
    user_id = auth.current_user["id"]
    query = "SELECT portfolio_id, name, cash_balance FROM Portfolio WHERE user_id = %s;"
    cursor.execute(query, (user_id,))
    portfolios = cursor.fetchall()
    
    print(style_label("\n----------------------------"))
    if portfolios:
        print(style_label("Your Portfolios:"))
        for portfolio in portfolios:
            print(style_info(f"Name: {portfolio[1]}, Cash Balance: ${float(portfolio[2]):,.2f}"))
    else:
        print(style_info("You have no portfolios yet."))
    print(style_label("----------------------------"))
    return portfolios

def create_portfolio():
    user_id = auth.current_user["id"]
    name = input(style_input_prompt("Enter a name for your new portfolio: "))
    
    # Check if a portfolio with the same name already exists for this user
    query = "SELECT portfolio_id FROM Portfolio WHERE user_id = %s AND name = %s;"
    cursor.execute(query, (user_id, name))
    if cursor.fetchone():
        print(style_error("❌ You already have a portfolio with that name. Please choose a different name."))
        sleep(1)
        return

    initial_balance = 0.00
    query = "INSERT INTO Portfolio (user_id, name, cash_balance) VALUES (%s, %s, %s) RETURNING portfolio_id;"
    cursor.execute(query, (user_id, name, initial_balance))
    portfolio_id = cursor.fetchone()[0]
    conn.commit()
    print(style_success(f"✅ Portfolio '{name}' created successfully"))
    sleep(1)
    
def open_portfolio(portfolios):
    # Instead of picking a number, ask the user for the portfolio name
    name = input(style_input_prompt("Enter the name of the portfolio you want to open: "))
    matched_portfolio = None
    for portfolio in portfolios:
         if portfolio[1].lower() == name.lower():
              matched_portfolio = portfolio
              break
    if matched_portfolio:
         portfolio_id = matched_portfolio[0]
         portfolio_menu.view_portfolio_menu(portfolio_id)
    else:
         print(style_error("❌ Portfolio name not found. Please check the name and try again."))
         sleep(1)
