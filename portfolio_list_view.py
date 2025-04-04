import auth
from db import conn, cursor
import portfolio_view
from time import sleep


def portfolio_menu():
    while True:
        # Display the user's current portfolios and capture them
        portfolios = display_portfolios()
        
        # Present the portfolio functionality menu
        print("\n📁 Portfolio Menu:")
        print("1. 🆕 Create Portfolio")
        if portfolios:
            print("2. 🔍 Open Portfolio")
            print("3. 🔙 Go Back")
        else:
            print("2. 🔙 Go Back")
            
        choice = input("Choose an option: ")
        
        if choice == "1":
            create_portfolio()
        elif choice == "2" and portfolios:
            open_portfolio(portfolios)
        elif (choice == "2" and not portfolios) or (choice == "3" and portfolios):
            # Exit the portfolio menu and return to the main menu
            break
        else:
            print("❌ Invalid option, please try again.")

def display_portfolios():
    user_id = auth.current_user["id"]
    query = "SELECT portfolio_id, name, cash_balance FROM Portfolio WHERE user_id = %s;"
    cursor.execute(query, (user_id,))
    portfolios = cursor.fetchall()
    
    if portfolios:
        print("\nYour Portfolios:")
        # Number each portfolio for easier selection
        for idx, portfolio in enumerate(portfolios, start=1):
            print(f"{idx}. Name: {portfolio[1]}, Cash Balance: ${float(portfolio[2]):,.2f}")
    else:
        print("\nYou have no portfolios yet.")
    return portfolios

def create_portfolio():
    user_id = auth.current_user["id"]
    name = input("Enter a name for your new portfolio: ")
    
    # Check if a portfolio with the same name already exists for this user
    query = "SELECT portfolio_id FROM Portfolio WHERE user_id = %s AND name = %s;"
    cursor.execute(query, (user_id, name))
    if cursor.fetchone():
        print("❌ You already have a portfolio with that name. Please choose a different name.")
        sleep(1)
        return

    initial_balance = 0.00
    query = "INSERT INTO Portfolio (user_id, name, cash_balance) VALUES (%s, %s, %s) RETURNING portfolio_id;"
    cursor.execute(query, (user_id, name, initial_balance))
    portfolio_id = cursor.fetchone()[0]
    conn.commit()
    print(f"✅ Portfolio '{name}' created successfully")
    sleep(1)
    

def open_portfolio(portfolios):
    choice = input("Enter the number of the portfolio you want to open: ")
    try:
        index = int(choice)
        if 1 <= index <= len(portfolios):
            portfolio_id = portfolios[index - 1][0]
            # Import the new portfolio view and display the chosen portfolio
            portfolio_view.view_portfolio_menu(portfolio_id)
        else:
            print("❌ Invalid portfolio number.")
            sleep(1)
    except ValueError:
        print("❌ Please enter a valid number.")
        sleep(1)

