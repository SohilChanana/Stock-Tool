import auth
from db import conn, cursor
from time import sleep

def view_portfolio_menu(portfolio_id):
    while True:
        # Refresh portfolio info on each loop iteration
        query = "SELECT name, cash_balance FROM Portfolio WHERE portfolio_id = %s;"
        cursor.execute(query, (portfolio_id,))
        result = cursor.fetchone()
        if not result:
            print("Portfolio not found.")
            return

        name, cash_balance = result
        print(f"\n📂 Portfolio: {name}")
        print(f"💵 Cash Balance: ${float(cash_balance):,.2f}")

        # Refresh and display stocks in this portfolio
        query = "SELECT symbol, shares FROM Portfolio_Contains WHERE portfolio_id = %s;"
        cursor.execute(query, (portfolio_id,))
        stocks = cursor.fetchall()
        
        if stocks:
            print("\nStocks in Portfolio:")
            for symbol, shares in stocks:
                print(f"- {symbol}: {shares} shares")
        else:
            print("\nNo stocks in this portfolio.")

        # Display portfolio view menu with additional options
        print("\n📊 Portfolio View Menu:")
        print("1. 💰 Deposit Cash")
        print("2. 💸 Withdraw Cash")
        print("3. 🛒 Buy Stock (Not implemented yet)")
        print("4. 📈 View Portfolio Stats (Not implemented yet)")
        print("5. ⏳ View Historical Stock Prices (Not implemented yet)")
        print("6. 🔮 View Future Stock Prices (Not implemented yet)")
        print("7. 🔙 Go Back")
        
        choice = input("Choose an option: ")
        
        if choice == "1":
            deposit_cash(portfolio_id)
        elif choice == "2":
            withdraw_cash(portfolio_id)
        elif choice in ("3", "4", "5", "6"):
            print("Option not implemented yet.")
            sleep(1)
        elif choice == "7":
            break
        else:
            print("❌ Invalid option, please try again.")
            sleep(1)

def deposit_cash(portfolio_id):
    try:
        amount = float(input("Enter the amount to deposit: "))
        if amount <= 0:
            print("❌ Amount must be positive.")
            sleep(1)
            return
        # Update portfolio cash balance
        update_query = "UPDATE Portfolio SET cash_balance = cash_balance + %s WHERE portfolio_id = %s;"
        cursor.execute(update_query, (amount, portfolio_id))
        
        # Create a cash transaction entry
        insert_query = """
            INSERT INTO Cash_Transaction (portfolio_id, type, amount, date)
            VALUES (%s, 'deposit', %s, CURRENT_DATE);
        """
        cursor.execute(insert_query, (portfolio_id, amount))
        conn.commit()
        print(f"✅ Deposited ${amount:,.2f} successfully.")
        sleep(1)
    except ValueError:
        print("❌ Invalid amount.")
        sleep(1)

def withdraw_cash(portfolio_id):
    try:
        amount = float(input("Enter the amount to withdraw: "))
        if amount <= 0:
            print("❌ Amount must be positive.")
            sleep(1)
            return
        # Check current cash balance
        query = "SELECT cash_balance FROM Portfolio WHERE portfolio_id = %s;"
        cursor.execute(query, (portfolio_id,))
        current_balance = cursor.fetchone()[0]
        if amount > float(current_balance):
            print("❌ Insufficient funds to withdraw that amount.")
            sleep(1)
            return
        
        # Update portfolio cash balance
        update_query = "UPDATE Portfolio SET cash_balance = cash_balance - %s WHERE portfolio_id = %s;"
        cursor.execute(update_query, (amount, portfolio_id))
        
        # Create a cash transaction entry
        insert_query = """
            INSERT INTO Cash_Transaction (portfolio_id, type, amount, date)
            VALUES (%s, 'withdrawal', %s, CURRENT_DATE);
        """
        cursor.execute(insert_query, (portfolio_id, amount))
        conn.commit()
        print(f"✅ Withdrew ${amount:,.2f} successfully.")
        sleep(1)
    except ValueError:
        print("❌ Invalid amount.")
        sleep(1)
