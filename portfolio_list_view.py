import auth
from db import conn, cursor

def portfolio_menu():
    while True:
        # Display the user's current portfolios
        display_portfolios()
        
        # Present the portfolio functionality menu
        print("\n📁 Portfolio Menu:")
        print("1. 🆕 Create Portfolio")
        print("2. 🔙 Go Back")
        choice = input("Choose an option: ")
        
        if choice == "1":
            create_portfolio()
        elif choice == "2":
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
        for portfolio in portfolios:
            print(f"Name: {portfolio[1]}, Cash Balance: ${float(portfolio[2]):,.2f}")
    else:
        print("\nYou have no portfolios yet.")

def create_portfolio():
    user_id = auth.current_user["id"]
    name = input("Enter a name for your new portfolio: ")
    
    # Check if a portfolio with the same name already exists for this user
    query = "SELECT portfolio_id FROM Portfolio WHERE user_id = %s AND name = %s;"
    cursor.execute(query, (user_id, name))
    if cursor.fetchone():
        print("❌ You already have a portfolio with that name. Please choose a different name.")
        return

    initial_balance = 0.00
    query = "INSERT INTO Portfolio (user_id, name, cash_balance) VALUES (%s, %s, %s) RETURNING portfolio_id;"
    cursor.execute(query, (user_id, name, initial_balance))
    portfolio_id = cursor.fetchone()[0]
    conn.commit()
    print(f"Portfolio '{name}' created successfully with ID {portfolio_id}.")

if __name__ == "__main__":
    if auth.current_user.get("id"):
        portfolio_menu()
    else:
        print("Please login to view your portfolios.")
