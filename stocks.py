import auth
from db import conn, cursor
from datetime import datetime, timedelta
from time import sleep
import plotext as plt
import pandas as pd
from sklearn.linear_model import LinearRegression
from ansi_format import style_input_prompt, style_error, style_success, style_label, style_info, style_menu_option

def add_daily_stock_data():
    """
    Add daily stock data to the database.
    """
    symbol = input(style_input_prompt("Enter the stock symbol (max 5 characters): ")).upper()
    if len(symbol) > 5:
        print(style_error("❌ Symbol is too long. Operation cancelled."))
        sleep(1)
        return

    # Check if the stock symbol exists in the Stock table.
    cursor.execute("SELECT symbol FROM Stock WHERE symbol = %s;", (symbol,))
    stock_in_table = cursor.fetchone()

    # Determine the trade date.
    if stock_in_table:
        cursor.execute("SELECT MAX(trade_date) FROM Daily_Stock_Price WHERE symbol = %s;", (symbol,))
        result = cursor.fetchone()
        if result and result[0]:
            last_date = result[0]
            next_date = last_date + timedelta(days=1)
            print(style_info(f"Last recorded trade date for {symbol} is {last_date}. Using next date: {next_date}."))
        else:
            date_str = input(style_input_prompt("No daily stock data found for this symbol. Enter the trade date (YYYY-MM-DD): "))
            try:
                next_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                print(style_error("❌ Invalid date format. Operation cancelled."))
                sleep(1)
                return
    else:
        date_str = input(style_input_prompt("Stock not in our system. Enter the trade date (YYYY-MM-DD): "))
        try:
            next_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            print(style_error("❌ Invalid date format. Operation cancelled."))
            sleep(1)
            return

    # Prompt for the stock prices and volume, ensuring numeric values.
    try:
        high = float(input(style_input_prompt("Enter the high price: ")))
        low = float(input(style_input_prompt("Enter the low price: ")))
        open_price = float(input(style_input_prompt("Enter the open price: ")))
        close_price = float(input(style_input_prompt("Enter the close price: ")))
        volume = int(input(style_input_prompt("Enter the volume: ")))
    except ValueError:
        print(style_error("❌ Invalid numeric input. Operation cancelled."))
        sleep(1)
        return

    # Display the entered data for user confirmation.
    print("\n" + style_label("Please confirm the following details:"))
    print(f"{style_label('Trade Date:')} {next_date}")
    print(f"{style_label('Symbol:')} {symbol}")
    print(f"{style_label('High Price:')} {high}")
    print(f"{style_label('Low Price:')} {low}")
    print(f"{style_label('Open Price:')} {open_price}")
    print(f"{style_label('Close Price:')} {close_price}")
    print(f"{style_label('Volume:')} {volume}")
    confirm = input(style_input_prompt("\nDo you want to add this data to the dataset? (y/n): "))
    if confirm.lower() != 'y':
        print(style_error("❌ Operation cancelled by user."))
        sleep(1)
        return

    # If the stock symbol doesn't exist in the Stock table, add it.
    if not stock_in_table:
        try:
            cursor.execute("INSERT INTO Stock (symbol) VALUES (%s);", (symbol,))
            conn.commit()
            print(style_success(f"✅ Stock symbol '{symbol}' added to Stock table."))
            sleep(1)
        except Exception as e:
            conn.rollback()
            print(style_error(f"❌ Failed to add stock symbol: {e}"))
            sleep(1)
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
        print(style_success("✅ Daily stock data added successfully."))
        sleep(1)
    except Exception as e:
        conn.rollback()
        print(style_error(f"❌ Failed to add daily stock data: {e}"))
        sleep(1)

def buy_stock(portfolio_id):
    """
    Buy stocks for a given portfolio.
    """
    symbol = input(style_input_prompt("Enter the stock symbol you want to buy: ")).upper()
    
    # Check if the stock exists in the Stock table.
    cursor.execute("SELECT symbol FROM Stock WHERE symbol = %s;", (symbol,))
    if not cursor.fetchone():
        print(style_error("❌ Stock does not exist in our system."))
        sleep(1)
        return

    # Ask for number of shares.
    try:
        shares = int(input(style_input_prompt("Enter the number of shares to buy: ")))
        if shares <= 0:
            print(style_error("❌ Number of shares must be greater than 0."))
            sleep(1)
            return
    except ValueError:
        print(style_error("❌ Invalid input for number of shares."))
        sleep(1)
        return

    # Get the most recent close price for the stock.
    cursor.execute(
        "SELECT close FROM Daily_Stock_Price WHERE symbol = %s ORDER BY trade_date DESC LIMIT 1;",
        (symbol,)
    )
    price_result = cursor.fetchone()
    if not price_result:
        print(style_error("❌ No stock price data available for this symbol."))
        sleep(1)
        return
    close_price = price_result[0]
    total_cost = close_price * shares

    print(style_info(f"Stock: {symbol}, Shares: {shares}, Price per share: ${close_price:.2f}, Total cost: ${total_cost:.2f}"))
    confirm = input(style_input_prompt("Do you want to confirm the purchase? (y/n): ")).lower()
    if confirm != 'y':
        print(style_error("❌ Purchase cancelled."))
        sleep(1)
        return

    # Check if the portfolio has enough cash.
    cursor.execute("SELECT cash_balance FROM Portfolio WHERE portfolio_id = %s;", (portfolio_id,))
    portfolio = cursor.fetchone()
    if not portfolio:
        print(style_error("❌ Portfolio not found."))
        sleep(1)
        return
    cash_balance = float(portfolio[0])
    if cash_balance < total_cost:
        print(style_error("❌ Insufficient funds to complete this purchase."))
        sleep(1)
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
    print(style_success("✅ Purchase completed successfully."))
    sleep(1)

def sell_stock(portfolio_id):
    """
    Sell stocks from a given portfolio.
    """
    symbol = input(style_input_prompt("Enter the stock symbol you want to sell: ")).upper()
    
    # Check if the portfolio owns this stock.
    cursor.execute(
        "SELECT shares FROM Portfolio_Contains WHERE portfolio_id = %s AND symbol = %s;",
        (portfolio_id, symbol)
    )
    result = cursor.fetchone()
    if not result:
        print(style_error("❌ You do not own any shares of this stock."))
        sleep(1)
        return
    owned_shares = result[0]

    # Ask for number of shares to sell.
    try:
        shares = int(input(style_input_prompt("Enter the number of shares to sell: ")))
        if shares <= 0:
            print(style_error("❌ Number of shares must be greater than 0."))
            sleep(1)
            return
    except ValueError:
        print(style_error("❌ Invalid input for number of shares."))
        sleep(1)
        return

    if shares > owned_shares:
        print(style_error("❌ You do not own enough shares to complete this sale."))
        sleep(1)
        return

    # Get the most recent close price for the stock.
    cursor.execute(
        "SELECT close FROM Daily_Stock_Price WHERE symbol = %s ORDER BY trade_date DESC LIMIT 1;",
        (symbol,)
    )
    price_result = cursor.fetchone()
    if not price_result:
        print(style_error("❌ No stock price data available for this symbol."))
        sleep(1)
        return
    close_price = price_result[0]
    total_value = close_price * shares

    print(style_info(f"Stock: {symbol}, Shares: {shares}, Price per share: ${close_price:.2f}, Total value: ${total_value:.2f}"))
    confirm = input(style_input_prompt("Do you want to confirm the sale? (y/n): ")).lower()
    if confirm != 'y':
        print(style_error("❌ Sale cancelled."))
        sleep(1)
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
    print(style_success("✅ Sale completed successfully."))
    sleep(1)
    
def view_historical_stock_prices():
    """View historical stock prices for a given symbol and time interval."""
    symbol = input(style_input_prompt("Enter the stock symbol to view historical prices: ")).upper()
    
    cursor.execute("SELECT MAX(trade_date) FROM Daily_Stock_Price WHERE symbol = %s;", (symbol,))
    latest_date_row = cursor.fetchone()
    if not latest_date_row or not latest_date_row[0]:
        print(style_error("❌ No historical data found for this symbol."))
        sleep(1)
        return
    latest_date = latest_date_row[0]
    
    print(style_label("Select the time interval:"))
    print(style_menu_option("1. Week"))
    print(style_menu_option("2. Month"))
    print(style_menu_option("3. Quarter"))
    print(style_menu_option("4. Year"))
    print(style_menu_option("5. 5 Years"))
    interval_choice = input(style_input_prompt("Choose an option (1-5): "))
    
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
        print(style_error("❌ Invalid interval choice."))
        sleep(1)
        return
    
    start_date = latest_date - delta

    query = """
        SELECT trade_date, close FROM Daily_Stock_Price
        WHERE symbol = %s AND trade_date BETWEEN %s AND %s
        ORDER BY trade_date ASC;
    """
    cursor.execute(query, (symbol, start_date, latest_date))
    data = cursor.fetchall()
    if not data:
        print(style_error("❌ No data available for the selected interval."))
        sleep(1)
        return
    
    dates = [row[0] for row in data]
    prices = [row[1] for row in data]
    dates_str = [d.strftime("%Y-%m-%d") for d in dates]
    
    plt.clear_figure()
    plt.date_form('Y-m-d')
    plt.plot(dates_str, prices, marker="hd", color="green")
    plt.title(f"Historical Prices for {symbol}")
    plt.xlabel("Trade Date")
    plt.ylabel("Close Price")
    plt.theme("dark")
    plt.show()
    
def view_future_stock_prices():
    """View future stock prices for a given symbol using a simple linear regression model."""
    symbol = input(style_input_prompt("Enter the stock symbol to view future prices: ")).upper()
    
    cursor.execute("SELECT MAX(trade_date) FROM Daily_Stock_Price WHERE symbol = %s;", (symbol,))
    latest_date_row = cursor.fetchone()
    if not latest_date_row or not latest_date_row[0]:
        print(style_error("❌ No historical data found for this symbol."))
        sleep(1)
        return
    latest_date = latest_date_row[0]
    
    print(style_label("Select the future time interval:"))
    print(style_menu_option("1. Week"))
    print(style_menu_option("2. Month"))
    print(style_menu_option("3. Quarter"))
    print(style_menu_option("4. Year"))
    print(style_menu_option("5. 5 Years"))
    interval_choice = input(style_input_prompt("Choose an option (1-5): "))
    
    if interval_choice == "1":
        future_dates = [latest_date + timedelta(days=i) for i in range(1, 8)]
    elif interval_choice == "2":
        future_dates = pd.date_range(start=latest_date + timedelta(days=1), periods=4, freq='W').to_pydatetime().tolist()
    elif interval_choice == "3":
        future_dates = pd.date_range(start=latest_date + timedelta(days=1), periods=13, freq='W').to_pydatetime().tolist()
    elif interval_choice == "4":
        future_dates = pd.date_range(start=latest_date + timedelta(days=1), periods=12, freq='MS').to_pydatetime().tolist()
    elif interval_choice == "5":
        future_dates = pd.date_range(start=latest_date + timedelta(days=1), periods=60, freq='MS').to_pydatetime().tolist()
    else:
        print(style_error("❌ Invalid interval choice."))
        sleep(1)
        return
    
    query = """
        SELECT trade_date, close FROM Daily_Stock_Price
        WHERE symbol = %s
        ORDER BY trade_date ASC;
    """
    cursor.execute(query, (symbol,))
    data = cursor.fetchall()
    if not data:
        print(style_error("❌ No historical data available for this symbol."))
        sleep(1)
        return
    
    df = pd.DataFrame(data, columns=["trade_date", "close"])
    df["date_ordinal"] = df["trade_date"].apply(lambda x: x.toordinal())
    
    X = df["date_ordinal"].values.reshape(-1, 1)
    y = df["close"].values
    
    model = LinearRegression()
    model.fit(X, y)
    
    future_ordinals = [d.toordinal() for d in future_dates]
    X_future = pd.DataFrame(future_ordinals)
    predictions = model.predict(X_future)
    
    future_dates_str = [d.strftime("%Y-%m-%d") for d in future_dates]
    future_prices = predictions.tolist()
    
    plt.clear_figure()
    plt.date_form('Y-m-d')
    plt.plot(future_dates_str, future_prices, marker="hd", color="yellow")
    plt.title(f"Future Prices for {symbol} (Linear Regression Forecast)")
    plt.xlabel("Date")
    plt.ylabel("Predicted Close Price")
    plt.theme("dark")
    plt.show()

def view_stock_stats():
    """
    View the coefficient of variation and beta for a given stock symbol.
    """
    stock_symbol = input(style_input_prompt("Enter the stock symbol: ")).upper().strip()
    
    cursor.execute("SELECT symbol FROM Stock WHERE symbol = %s;", (stock_symbol,))
    if not cursor.fetchone():
        print(style_error("❌ Stock symbol not found in the database."))
        sleep(1)
        return

    cursor.execute("""
        SELECT coefficient_of_variation, beta, last_updated
        FROM Stock_Stats_Cache
        WHERE symbol = %s;
    """, (stock_symbol,))
    cached_result = cursor.fetchone()
    
    if cached_result:
        cv, beta, last_updated = cached_result
        print(style_label(f"\nStatistics for {stock_symbol} (based on 5 years of data):"))
        print(style_info(f"Coefficient of Variation: {cv:.4f}"))
        print(style_info(f"Beta: {beta:.4f}"))
        return

    stats_query = """
        WITH stock_data AS (
            SELECT trade_date,
                   (close - LAG(close) OVER (ORDER BY trade_date)) / LAG(close) OVER (ORDER BY trade_date) AS daily_return
            FROM Daily_Stock_Price
            WHERE symbol = %s
        ),
        cv_calc AS (
            SELECT AVG(daily_return) AS mean_return,
                   STDDEV_POP(daily_return) AS stddev_return,
                   STDDEV_POP(daily_return) / AVG(daily_return) AS coefficient_of_variation
            FROM stock_data
            WHERE daily_return IS NOT NULL
        ),
        market_data AS (
            SELECT trade_date,
                   SUM(close) AS market_close
            FROM Daily_Stock_Price
            GROUP BY trade_date
            ORDER BY trade_date
        ),
        market_returns AS (
            SELECT trade_date,
                   (market_close - LAG(market_close) OVER (ORDER BY trade_date)) / LAG(market_close) OVER (ORDER BY trade_date) AS market_daily_return
            FROM market_data
        ),
        beta_calc AS (
            SELECT covar_pop(s.daily_return, m.market_daily_return) / var_pop(m.market_daily_return) AS beta
            FROM stock_data s
            JOIN market_returns m ON s.trade_date = m.trade_date
            WHERE s.daily_return IS NOT NULL AND m.market_daily_return IS NOT NULL
        )
        SELECT cv.coefficient_of_variation, beta.beta
        FROM cv_calc cv, beta_calc beta;
    """
    
    cursor.execute(stats_query, (stock_symbol,))
    result = cursor.fetchone()
    
    if not result:
        print(style_error("❌ Failed to compute statistics for the stock."))
        sleep(1)
        return
    
    cv, beta = result

    cursor.execute("""
        INSERT INTO Stock_Stats_Cache (symbol, coefficient_of_variation, beta, last_updated)
        VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (symbol)
        DO UPDATE SET 
            coefficient_of_variation = EXCLUDED.coefficient_of_variation,
            beta = EXCLUDED.beta,
            last_updated = EXCLUDED.last_updated;
    """, (stock_symbol, cv, beta))
    conn.commit()

    print(style_label(f"\nStatistics for {stock_symbol} (based on 5 years of data):"))
    print(style_info(f"Coefficient of Variation: {cv:.4f}"))
    print(style_info(f"Beta: {beta:.4f}"))
    
def get_pair_correlation(symbol1, symbol2):
    """
    Computes the correlation between two stock symbols.
    If the correlation is already cached, it retrieves it from the cache.
    """
    s1, s2 = (symbol1, symbol2) if symbol1 < symbol2 else (symbol2, symbol1)
    cursor.execute("""
        SELECT correlation FROM Correlation_Cache
        WHERE symbol_a = %s AND symbol_b = %s;
    """, (s1, s2))
    result = cursor.fetchone()
    if result is not None:
        return result[0]

    correlation_query = """
        WITH stock1 AS (
            SELECT trade_date,
                   (close - LAG(close) OVER (ORDER BY trade_date)) / LAG(close) OVER (ORDER BY trade_date) AS daily_return
            FROM Daily_Stock_Price
            WHERE symbol = %s
        ),
        stock2 AS (
            SELECT trade_date,
                   (close - LAG(close) OVER (ORDER BY trade_date)) / LAG(close) OVER (ORDER BY trade_date) AS daily_return
            FROM Daily_Stock_Price
            WHERE symbol = %s
        )
        SELECT corr(s1.daily_return, s2.daily_return) AS correlation
        FROM stock1 s1
        JOIN stock2 s2 ON s1.trade_date = s2.trade_date
        WHERE s1.daily_return IS NOT NULL AND s2.daily_return IS NOT NULL;
    """
    cursor.execute(correlation_query, (symbol1, symbol2))
    result = cursor.fetchone()
    corr_value = result[0] if result is not None else None

    if corr_value is not None:
        cursor.execute("""
            INSERT INTO Correlation_Cache (symbol_a, symbol_b, correlation, last_updated)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (symbol_a, symbol_b)
            DO UPDATE SET correlation = EXCLUDED.correlation,
                          last_updated = EXCLUDED.last_updated;
        """, (s1, s2, corr_value))
        conn.commit()

    return corr_value

def view_portfolio_stats(portfolio_id):
    """
    Retrieves all stocks in the portfolio, calculates pairwise correlation for each pair
    (using cached values when available), and displays the correlation matrix.
    """
    cursor.execute("SELECT symbol FROM Portfolio_Contains WHERE portfolio_id = %s;", (portfolio_id,))
    rows = cursor.fetchall()
    if not rows:
        print(style_error("❌ No stocks in portfolio."))
        return

    symbols = sorted([row[0] for row in rows])
    n = len(symbols)
    matrix = {symbol: {s: None for s in symbols} for symbol in symbols}

    for i in range(n):
        for j in range(i, n):
            if i == j:
                matrix[symbols[i]][symbols[j]] = 1.0
            else:
                corr_val = get_pair_correlation(symbols[i], symbols[j])
                if corr_val is None:
                    corr_val = 0.0
                matrix[symbols[i]][symbols[j]] = corr_val
                matrix[symbols[j]][symbols[i]] = corr_val

    print(style_label("\nCorrelation Matrix:"))
    header = "         " + "  ".join([f"{sym:>8}" for sym in symbols])
    print(header)
    for sym in symbols:
        row_str = f"{sym:>8}"
        for sym2 in symbols:
            row_str += f"  {matrix[sym][sym2]:8.4f}"
        print(row_str)

def view_list_stats(list_id):
    """
    Retrieves all stocks in the stock list (from the List_Contains table),
    calculates pairwise correlations for each pair (using cached values when available),
    and displays the correlation matrix.
    """
    cursor.execute("SELECT symbol FROM List_Contains WHERE list_id = %s;", (list_id,))
    rows = cursor.fetchall()
    if not rows:
        print(style_error("❌ No stocks in the list."))
        return

    symbols = sorted([row[0] for row in rows])
    n = len(symbols)
    matrix = {symbol: {s: None for s in symbols} for symbol in symbols}

    for i in range(n):
        for j in range(i, n):
            if i == j:
                matrix[symbols[i]][symbols[j]] = 1.0
            else:
                corr_val = get_pair_correlation(symbols[i], symbols[j])
                if corr_val is None:
                    corr_val = 0.0
                matrix[symbols[i]][symbols[j]] = corr_val
                matrix[symbols[j]][symbols[i]] = corr_val

    print(style_label("\nCorrelation Matrix for Stock List:"))
    header = "         " + "  ".join([f"{sym:>8}" for sym in symbols])
    print(header)
    for sym in symbols:
        row_str = f"{sym:>8}"
        for sym2 in symbols:
            row_str += f"  {matrix[sym][sym2]:8.4f}"
        print(row_str)
