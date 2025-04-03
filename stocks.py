import auth
from db import conn, cursor
from datetime import datetime
from time import sleep

def add_daily_stock_data():
    # Prompt for trade date and validate format.
    date_str = input("Enter the trade date (YYYY-MM-DD): ")
    try:
        trade_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        print("❌ Invalid date format. Operation cancelled.")
        sleep(1)
        return

    # Prompt for stock symbol and validate length.
    symbol = input("Enter the stock symbol (max 5 characters): ").upper()
    if len(symbol) > 5:
        print("❌ Symbol is too long. Operation cancelled.")
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

    # If the stock symbol doesn't exist in the Stock table, add it.
    cursor.execute("SELECT symbol FROM Stock WHERE symbol = %s;", (symbol,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO Stock (symbol) VALUES (%s);", (symbol,))
        print(f"✅ Stock symbol '{symbol}' added to Stock table.")
        sleep(1)

    # Insert the daily stock data into the Daily_Stock_Price table.
    try:
        query = """
            INSERT INTO Daily_Stock_Price (trade_date, symbol, high, low, open, close, volume)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        cursor.execute(query, (trade_date, symbol, high, low, open_price, close_price, volume))
        conn.commit()
        print("✅ Daily stock data added successfully.")
    except Exception as e:
        conn.rollback()
        print("❌ Failed to add daily stock data:", e)
        sleep(1)

# if __name__ == "__main__":
#     add_daily_stock_data()
