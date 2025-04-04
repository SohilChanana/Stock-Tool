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

