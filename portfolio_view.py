import auth
from db import conn, cursor
import stocks
from time import sleep
from datetime import timedelta

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
        print("\n----------------------------")
        print(f"📂 Portfolio: {name}")
        print(f"💵 Cash Balance: ${float(cash_balance):,.2f}")

        # Calculate the current market value of stocks in the portfolio.
        total_stocks_value = 0.0
        query = "SELECT symbol, shares FROM Portfolio_Contains WHERE portfolio_id = %s;"
        cursor.execute(query, (portfolio_id,))
        stocks_in_portfolio = cursor.fetchall()
        
        if stocks_in_portfolio:
            print("\nStocks in Portfolio:")
            for symbol, shares in stocks_in_portfolio:
                # Get the most recent close price for the stock.
                cursor.execute(
                    "SELECT close FROM Daily_Stock_Price WHERE symbol = %s ORDER BY trade_date DESC LIMIT 1;",
                    (symbol,)
                )
                price_result = cursor.fetchone()
                if price_result:
                    close_price = price_result[0]
                else:
                    close_price = 0.0
                stock_value = shares * close_price
                total_stocks_value += stock_value
                print(f"- {symbol}: {shares} shares, Share Price: ${close_price:,.2f}")
        else:
            print("\nNo stocks in this portfolio.")

        total_portfolio_value = float(cash_balance) + total_stocks_value
        print(f"\n🏦 Total Portfolio Market Value: ${total_portfolio_value:,.2f}")
        print("----------------------------")

        # Display portfolio view menu with updated options.
        print("\n📊 Portfolio View Menu:")
        print("1. 💰 Deposit Cash")
        print("2. 💸 Withdraw Cash")
        print("3. 🛒 Buy Stock")
        print("4. 🏷️  Sell Stock")
        print("5. 📈 View Portfolio Stats (Not implemented yet)")
        print("6. ⏳ View Historical Stock Prices")
        print("7. 🔮 View Future Stock Prices (Not implemented yet)")
        print("8. 🔙 Go Back")
        
        choice = input("Choose an option: ")
        
        if choice == "1":
            deposit_cash(portfolio_id)
        elif choice == "2":
            withdraw_cash(portfolio_id)
        elif choice == "3":
            stocks.buy_stock(portfolio_id)
        elif choice == "4":
            stocks.sell_stock(portfolio_id)
        elif choice == "5":
            print("Option not implemented yet.")
            sleep(1)
        elif choice == "6":
            stocks.view_historical_stock_prices()
        elif choice == "7":
            print("Option not implemented yet.")
            sleep(1)
        elif choice == "8":
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


