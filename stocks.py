import auth
from db import conn, cursor
from datetime import datetime, timedelta
from time import sleep
import plotext as plt
import pandas as pd
from sklearn.linear_model import LinearRegression

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
    
def view_historical_stock_prices():
    """View historical stock prices for a given symbol and time interval."""

    # Ask for the stock symbol.
    symbol = input("Enter the stock symbol to view historical prices: ").upper()
    
    # Get the most recent trade date for the symbol.
    cursor.execute("SELECT MAX(trade_date) FROM Daily_Stock_Price WHERE symbol = %s;", (symbol,))
    latest_date_row = cursor.fetchone()
    if not latest_date_row or not latest_date_row[0]:
        print("❌ No historical data found for this symbol.")
        return
    latest_date = latest_date_row[0]
    
    # Ask the user for the desired time interval.
    print("Select the time interval:")
    print("1. Week")
    print("2. Month")
    print("3. Quarter")
    print("4. Year")
    print("5. 5 Years")
    interval_choice = input("Choose an option (1-5): ")
    
    if interval_choice == "1":
        delta = timedelta(days=7)
    elif interval_choice == "2":
        delta = timedelta(days=30)
    elif interval_choice == "3":
        delta = timedelta(days=90)
    elif interval_choice == "4":
        delta = timedelta(days=365)
    elif interval_choice == "5":
        delta = timedelta(days=5*365)
    else:
        print("❌ Invalid interval choice.")
        return
    
    start_date = latest_date - delta

    # Query historical data between start_date and the latest available date.
    query = """
        SELECT trade_date, close FROM Daily_Stock_Price
        WHERE symbol = %s AND trade_date BETWEEN %s AND %s
        ORDER BY trade_date ASC;
    """
    cursor.execute(query, (symbol, start_date, latest_date))
    data = cursor.fetchall()
    if not data:
        print("❌ No data available for the selected interval.")
        return
    
    # Prepare data for plotting.
    dates = [row[0] for row in data]
    prices = [row[1] for row in data]
    # Convert date objects to strings.
    dates_str = [d.strftime("%Y-%m-%d") for d in dates]
    
    # Plot using plotext.
    plt.clear_figure()
    plt.date_form('Y-m-d')
    plt.plot(dates_str, prices, marker="hd", color="green", )
    plt.title(f"Historical Prices for {symbol}")
    plt.xlabel("Trade Date")
    plt.ylabel("Close Price")
    plt.theme("dark")
    plt.show()
    
def view_future_stock_prices():
    """View future stock prices for a given symbol using a simple linear regression model."""
    # Ask for the stock symbol.
    symbol = input("Enter the stock symbol to view future prices: ").upper()
    
    # Get the latest available trade date for the symbol.
    cursor.execute("SELECT MAX(trade_date) FROM Daily_Stock_Price WHERE symbol = %s;", (symbol,))
    latest_date_row = cursor.fetchone()
    if not latest_date_row or not latest_date_row[0]:
        print("❌ No historical data found for this symbol.")
        return
    latest_date = latest_date_row[0]
    
    # Ask for the desired future time interval.
    print("Select the future time interval:")
    print("1. Week")
    print("2. Month")
    print("3. Quarter")
    print("4. Year")
    print("5. 5 Years")
    interval_choice = input("Choose an option (1-5): ")
    
    # Generate future dates based on the selected interval.
    if interval_choice == "1":
        # For one week: daily data (7 days).
        future_dates = [latest_date + timedelta(days=i) for i in range(1, 8)]
    elif interval_choice == "2":
        # For one month: weekly data (4 data points).
        future_dates = pd.date_range(start=latest_date + timedelta(days=1), periods=4, freq='W').to_pydatetime().tolist()
    elif interval_choice == "3":
        # For one quarter: weekly data (approximately 13 data points).
        future_dates = pd.date_range(start=latest_date + timedelta(days=1), periods=13, freq='W').to_pydatetime().tolist()
    elif interval_choice == "4":
        # For one year: monthly data (12 data points).
        future_dates = pd.date_range(start=latest_date + timedelta(days=1), periods=12, freq='MS').to_pydatetime().tolist()
    elif interval_choice == "5":
        # For 5 years: monthly data (60 data points).
        future_dates = pd.date_range(start=latest_date + timedelta(days=1), periods=60, freq='MS').to_pydatetime().tolist()
    else:
        print("❌ Invalid interval choice.")
        return
    
    # Query all historical data for the given stock symbol.
    query = """
        SELECT trade_date, close FROM Daily_Stock_Price
        WHERE symbol = %s
        ORDER BY trade_date ASC;
    """
    cursor.execute(query, (symbol,))
    data = cursor.fetchall()
    if not data:
        print("❌ No historical data available for this symbol.")
        return
    
    # Prepare the data for linear regression.
    df = pd.DataFrame(data, columns=["trade_date", "close"])
    # Convert trade_date to an ordinal number (numeric format) for regression.
    df["date_ordinal"] = df["trade_date"].apply(lambda x: x.toordinal())
    
    X = df["date_ordinal"].values.reshape(-1, 1)
    y = df["close"].values
    
    # Fit a linear regression model.
    model = LinearRegression()
    model.fit(X, y)
    
    # Generate predictions for the future dates.
    future_ordinals = [d.toordinal() for d in future_dates]
    X_future = pd.DataFrame(future_ordinals)
    predictions = model.predict(X_future)
    
    # Prepare data for plotting.
    future_dates_str = [d.strftime("%Y-%m-%d") for d in future_dates]
    future_prices = predictions.tolist()
    
    # Plot the forecast using plotext (similar to the historical data plot).
    plt.clear_figure()
    plt.date_form('Y-m-d')
    plt.plot(future_dates_str, future_prices, marker="hd", color="yellow")
    plt.title(f"Future Prices for {symbol} (Linear Regression Forecast)")
    plt.xlabel("Date")
    plt.ylabel("Predicted Close Price")
    plt.theme("dark")
    plt.show()
