import auth
from db import conn, cursor
import stocks
from time import sleep
from datetime import timedelta
from ansi_format import style_menu_option, style_input_prompt, style_error, style_success, style_label, style_info

def view_portfolio_menu(portfolio_id):
    while True:
        # Refresh portfolio info on each loop iteration
        query = "SELECT name, cash_balance FROM Portfolio WHERE portfolio_id = %s;"
        cursor.execute(query, (portfolio_id,))
        result = cursor.fetchone()
        if not result:
            print(style_error("Portfolio not found."))
            return

        name, cash_balance = result
        print(style_label("\n----------------------------"))
        print(style_label(f"📂 Portfolio: {name}"))
        print(style_label(f"💵 Cash Balance: ${float(cash_balance):,.2f}"))

        # Calculate the current market value of stocks in the portfolio.
        total_stocks_value = 0.0
        query = "SELECT symbol, shares FROM Portfolio_Contains WHERE portfolio_id = %s;"
        cursor.execute(query, (portfolio_id,))
        stocks_in_portfolio = cursor.fetchall()
        
        if stocks_in_portfolio:
            print("\n" + style_label("Stocks in Portfolio:"))
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
                # Using style_info for stock details:
                print(style_info(f"- {symbol}: {shares} shares, Share Price: ${close_price:,.2f}"))
        else:
            print("\n" + style_info("No stocks in this portfolio."))

        total_portfolio_value = float(cash_balance) + total_stocks_value
        print("\n" + style_label(f"🏦 Total Portfolio Market Value: ${total_portfolio_value:,.2f}"))
        print(style_label("----------------------------"))

        print("\n" + style_label("📊 Portfolio View Menu:"))
        print(style_menu_option("1. 💰 Deposit Cash"))
        print(style_menu_option("2. 💸 Withdraw Cash"))
        print(style_menu_option("3. 💱 Transfer Funds"))
        print(style_menu_option("4. 🛒 Buy Stock"))
        print(style_menu_option("5. 🏷️  Sell Stock"))
        print(style_menu_option("6. 📈 View Stock Stats"))
        print(style_menu_option("7. 📈 View Portfolio Stats"))
        print(style_menu_option("8. ⏳ View Historical Stock Prices"))
        print(style_menu_option("9. 🔮 Predict Future Stock Prices"))
        print(style_menu_option("10. 🔙 Go Back"))
        
        choice = input(style_input_prompt("Choose an option: "))
        
        if choice == "1":
            deposit_cash(portfolio_id)
        elif choice == "2":
            withdraw_cash(portfolio_id)
        elif choice == "3":
            transfer_funds(portfolio_id)
        elif choice == "4":
            stocks.buy_stock(portfolio_id)
        elif choice == "5":
            stocks.sell_stock(portfolio_id)
        elif choice == "6":
            stocks.view_stock_stats() 
        elif choice == "7":
            stocks.view_portfolio_stats(portfolio_id)
        elif choice == "8":
            stocks.view_historical_stock_prices()
        elif choice == "9":
            stocks.view_future_stock_prices()
        elif choice == "10":
            break
        else:
            print(style_error("❌ Invalid option, please try again."))
            sleep(1)


def deposit_cash(portfolio_id):
    try:
        amount = float(input(style_input_prompt("Enter the amount to deposit: ")))
        if amount <= 0:
            print(style_error("❌ Amount must be positive."))
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
        print(style_success(f"✅ Deposited ${amount:,.2f} successfully."))
        sleep(1)
    except ValueError:
        print(style_error("❌ Invalid amount."))
        sleep(1)


def withdraw_cash(portfolio_id):
    try:
        amount = float(input(style_input_prompt("Enter the amount to withdraw: ")))
        if amount <= 0:
            print(style_error("❌ Amount must be positive."))
            sleep(1)
            return
        # Check current cash balance
        query = "SELECT cash_balance FROM Portfolio WHERE portfolio_id = %s;"
        cursor.execute(query, (portfolio_id,))
        current_balance = cursor.fetchone()[0]
        if amount > float(current_balance):
            print(style_error("❌ Insufficient funds to withdraw that amount."))
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
        print(style_success(f"✅ Withdrew ${amount:,.2f} successfully."))
        sleep(1)
    except ValueError:
        print(style_error("❌ Invalid amount."))
        sleep(1)

def transfer_funds(portfolio_id):
    # Get the current portfolio's cash balance.
    query = "SELECT cash_balance FROM Portfolio WHERE portfolio_id = %s;"
    cursor.execute(query, (portfolio_id,))
    current_balance_row = cursor.fetchone()
    if not current_balance_row:
        print(style_error("❌ Current portfolio not found."))
        sleep(1)
        return
    current_balance = float(current_balance_row[0])
    
    # Ask for the target portfolio name.
    target_name = input(style_input_prompt("Enter the name of the portfolio to transfer funds to: ")).strip()
    # Assume the target portfolio belongs to the same user.
    user_id = auth.current_user["id"]
    query = "SELECT portfolio_id FROM Portfolio WHERE name = %s AND user_id = %s;"
    cursor.execute(query, (target_name, user_id))
    target_row = cursor.fetchone()
    if not target_row:
        print(style_error("❌ Target portfolio not found."))
        sleep(1)
        return
    target_portfolio_id = target_row[0]
    if target_portfolio_id == portfolio_id:
        print(style_error("❌ Cannot transfer funds to the same portfolio."))
        sleep(1)
        return
    
    # Ask for the amount to transfer.
    try:
        amount = float(input(style_input_prompt("Enter the amount to transfer: ")))
        if amount <= 0:
            print(style_error("❌ Amount must be positive."))
            sleep(1)
            return
    except ValueError:
        print(style_error("❌ Invalid amount."))
        sleep(1)
        return
    
    # Check if the current portfolio has sufficient funds.
    if amount > current_balance:
        print(style_error("❌ Insufficient funds to complete this transfer."))
        sleep(1)
        return
    
    # Ask for confirmation.
    confirm = input(style_input_prompt(f"Confirm transfer of ${amount:,.2f} to portfolio '{target_name}'? (y/n): ")).lower()
    if confirm != 'y':
        print(style_error("❌ Transfer cancelled."))
        sleep(1)
        return
    
    # Deduct funds from the current portfolio.
    update_source = "UPDATE Portfolio SET cash_balance = cash_balance - %s WHERE portfolio_id = %s;"
    cursor.execute(update_source, (amount, portfolio_id))
    # Add funds to the target portfolio.
    update_target = "UPDATE Portfolio SET cash_balance = cash_balance + %s WHERE portfolio_id = %s;"
    cursor.execute(update_target, (amount, target_portfolio_id))
    # Insert a cash transaction record with type 'transfer' and transfer_dest_id.
    insert_transaction = """
        INSERT INTO Cash_Transaction (portfolio_id, type, amount, date, transfer_dest_id)
        VALUES (%s, 'transfer', %s, CURRENT_DATE, %s);
    """
    cursor.execute(insert_transaction, (portfolio_id, amount, target_portfolio_id))
    
    conn.commit()
    print(style_success(f"✅ Transferred ${amount:,.2f} to portfolio '{target_name}' successfully."))
    sleep(1)
