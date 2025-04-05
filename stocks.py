import auth
from db import conn, cursor
from datetime import datetime, timedelta
from time import sleep

def add_daily_stock_data():
    # Prompt for stock symbol and validate its length.
    symbol = input("Enter the stock symbol (max 5 characters): ").upper()
    if len(symbol) > 5:
        print("❌ Symbol is too long. Operation cancelled.")
        sleep(1)
        return

    # Check if the stock symbol exists in the Stock table.
    cursor.execute("SELECT symbol FROM Stock WHERE symbol = %s;", (symbol,))
    stock_in_table = cursor.fetchone()

    # Determine the trade date.
    if stock_in_table:
        # Stock exists: get the most recent trade date.
        cursor.execute("SELECT MAX(trade_date) FROM Daily_Stock_Price WHERE symbol = %s;", (symbol,))
        result = cursor.fetchone()
        if result and result[0]:
            last_date = result[0]
            next_date = last_date + timedelta(days=1)
            print(f"Last recorded trade date for {symbol} is {last_date}. Using next date: {next_date}.")
        else:
            # No daily stock data exists for this stock.
            date_str = input("No daily stock data found for this symbol. Enter the trade date (YYYY-MM-DD): ")
            try:
                next_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                print("❌ Invalid date format. Operation cancelled.")
                sleep(1)
                return
    else:
        # Stock not in our system: ask user for a trade date.
        date_str = input("Stock not in our system. Enter the trade date (YYYY-MM-DD): ")
        try:
            next_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            print("❌ Invalid date format. Operation cancelled.")
            sleep(1)
            return

    # Prompt for the stock prices and volume, ensuring numeric values.
    try:
        high = float(input("Enter the high price: "))
        low = float(input("Enter the low price: "))
        open_price = float(input("Enter the open price: "))
        close_price = float(input("Enter the close price: "))
        volume = int(input("Enter the volume: "))
    except ValueError:
        print("❌ Invalid numeric input. Operation cancelled.")
        sleep(1)
        return

    # Display the entered data for user confirmation with colored text.
    print("\n\033[1;33mPlease confirm the following details:\033[0m")  # Bold yellow header
    print("\033[1;34mTrade Date:\033[0m", next_date)
    print("\033[1;34mSymbol:\033[0m", symbol)
    print("\033[1;34mHigh Price:\033[0m", high)
    print("\033[1;34mLow Price:\033[0m", low)
    print("\033[1;34mOpen Price:\033[0m", open_price)
    print("\033[1;34mClose Price:\033[0m", close_price)
    print("\033[1;34mVolume:\033[0m", volume)
    confirm = input("\nDo you want to add this data to the dataset? (y/n): ")
    if confirm.lower() != 'y':
        print("❌ Operation cancelled by user.")
        return

    # If the stock symbol doesn't exist in the Stock table, add it.
    if not stock_in_table:
        try:
            cursor.execute("INSERT INTO Stock (symbol) VALUES (%s);", (symbol,))
            conn.commit()
            print(f"✅ Stock symbol '{symbol}' added to Stock table.")
        except Exception as e:
            conn.rollback()
            print("❌ Failed to add stock symbol:", e)
            return

    # Insert the daily stock data into the Daily_Stock_Price table.
    try:
        query = """
            INSERT INTO Daily_Stock_Price (trade_date, symbol, high, low, open, close, volume)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        cursor.execute(query, (
            next_date,
            symbol,
            high,
            low,
            open_price,
            close_price,
            volume
        ))
        conn.commit()
        print("✅ Daily stock data added successfully.")
    except Exception as e:
        conn.rollback()
        print("❌ Failed to add daily stock data:", e)
        sleep(1)

def buy_stock(portfolio_id):
    # Prompt for stock symbol
    symbol = input("Enter the stock symbol you want to buy: ").upper()
    
    # Check if the stock exists in the Stock table.
    cursor.execute("SELECT symbol FROM Stock WHERE symbol = %s;", (symbol,))
    if not cursor.fetchone():
        print("❌ Stock does not exist in our system.")
        return

    # Ask for number of shares.
    try:
        shares = int(input("Enter the number of shares to buy: "))
        if shares <= 0:
            print("❌ Number of shares must be greater than 0.")
            return
    except ValueError:
        print("❌ Invalid input for number of shares.")
        return

    # Get the most recent close price for the stock.
    cursor.execute(
        "SELECT close FROM Daily_Stock_Price WHERE symbol = %s ORDER BY trade_date DESC LIMIT 1;",
        (symbol,)
    )
    price_result = cursor.fetchone()
    if not price_result:
        print("❌ No stock price data available for this symbol.")
        return
    close_price = price_result[0]
    total_cost = close_price * shares

    print(f"Stock: {symbol}, Shares: {shares}, Price per share: ${close_price:.2f}, Total cost: ${total_cost:.2f}")
    confirm = input("Do you want to confirm the purchase? (y/n): ").lower()
    if confirm != 'y':
        print("❌ Purchase cancelled.")
        return

    # Check if the portfolio has enough cash.
    cursor.execute("SELECT cash_balance FROM Portfolio WHERE portfolio_id = %s;", (portfolio_id,))
    portfolio = cursor.fetchone()
    if not portfolio:
        print("❌ Portfolio not found.")
        return
    cash_balance = float(portfolio[0])
    if cash_balance < total_cost:
        print("❌ Insufficient funds to complete this purchase.")
        return

    # Insert the transaction into Stock_Transaction.
    cursor.execute(
        "INSERT INTO Stock_Transaction (portfolio_id, symbol, date, type, shares, price) VALUES (%s, %s, CURRENT_DATE, 'buy', %s, %s) RETURNING transaction_id;",
        (portfolio_id, symbol, shares, close_price)
    )

    # Update the Portfolio_Contains table.
    cursor.execute(
        "SELECT shares FROM Portfolio_Contains WHERE portfolio_id = %s AND symbol = %s;",
        (portfolio_id, symbol)
    )
    existing = cursor.fetchone()
    if existing:
        cursor.execute(
            "UPDATE Portfolio_Contains SET shares = shares + %s WHERE portfolio_id = %s AND symbol = %s;",
            (shares, portfolio_id, symbol)
        )
    else:
        cursor.execute(
            "INSERT INTO Portfolio_Contains (portfolio_id, symbol, shares) VALUES (%s, %s, %s);",
            (portfolio_id, symbol, shares)
        )

    # Deduct the total cost from the portfolio cash balance.
    cursor.execute(
        "UPDATE Portfolio SET cash_balance = cash_balance - %s WHERE portfolio_id = %s;",
        (total_cost, portfolio_id)
    )

    conn.commit()
    print("✅ Purchase completed successfully.")


def sell_stock(portfolio_id):
    # Prompt for the stock symbol.
    symbol = input("Enter the stock symbol you want to sell: ").upper()
    
    # Check if the portfolio owns this stock.
    cursor.execute(
        "SELECT shares FROM Portfolio_Contains WHERE portfolio_id = %s AND symbol = %s;",
        (portfolio_id, symbol)
    )
    result = cursor.fetchone()
    if not result:
        print("❌ You do not own any shares of this stock.")
        return
    owned_shares = result[0]

    # Ask for number of shares to sell.
    try:
        shares = int(input("Enter the number of shares to sell: "))
        if shares <= 0:
            print("❌ Number of shares must be greater than 0.")
            return
    except ValueError:
        print("❌ Invalid input for number of shares.")
        return

    if shares > owned_shares:
        print("❌ You do not own enough shares to complete this sale.")
        return

    # Get the most recent close price for the stock.
    cursor.execute(
        "SELECT close FROM Daily_Stock_Price WHERE symbol = %s ORDER BY trade_date DESC LIMIT 1;",
        (symbol,)
    )
    price_result = cursor.fetchone()
    if not price_result:
        print("❌ No stock price data available for this symbol.")
        return
    close_price = price_result[0]
    total_value = close_price * shares

    print(f"Stock: {symbol}, Shares: {shares}, Price per share: ${close_price:.2f}, Total value: ${total_value:.2f}")
    confirm = input("Do you want to confirm the sale? (y/n): ").lower()
    if confirm != 'y':
        print("❌ Sale cancelled.")
        return

    # Insert the transaction into Stock_Transaction.
    cursor.execute(
        "INSERT INTO Stock_Transaction (portfolio_id, symbol, date, type, shares, price) VALUES (%s, %s, CURRENT_DATE, 'sell', %s, %s) RETURNING transaction_id;",
        (portfolio_id, symbol, shares, close_price)
    )

    # Update the Portfolio_Contains table.
    new_share_count = owned_shares - shares
    if new_share_count > 0:
        cursor.execute(
            "UPDATE Portfolio_Contains SET shares = %s WHERE portfolio_id = %s AND symbol = %s;",
            (new_share_count, portfolio_id, symbol)
        )
    else:
        cursor.execute(
            "DELETE FROM Portfolio_Contains WHERE portfolio_id = %s AND symbol = %s;",
            (portfolio_id, symbol)
        )

    # Add the proceeds to the portfolio cash balance.
    cursor.execute(
        "UPDATE Portfolio SET cash_balance = cash_balance + %s WHERE portfolio_id = %s;",
        (total_value, portfolio_id)
    )

    conn.commit()
    print("✅ Sale completed successfully.")
