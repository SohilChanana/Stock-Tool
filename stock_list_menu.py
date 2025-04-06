import auth
from db import conn, cursor
from time import sleep

def view_stock_list_menu(list_id, is_creator):
    while True:
        # Get list details: name, creator, visibility
        query = """
            SELECT sl.name, u.username, sl.visibility
            FROM Stock_List sl
            JOIN Users u ON sl.user_id = u.user_id
            WHERE sl.list_id = %s;
        """
        cursor.execute(query, (list_id,))
        result = cursor.fetchone()
        if not result:
            print("List not found.")
            return
        name, creator, visibility = result
        print("\n----------------------------")
        print(f"📃 Stock List: {name}")
        print(f"👤 Created by: {creator}")
        print(f"🔒 Visibility: {visibility}")
        
        # Display stocks in the list and calculate total market value
        query = "SELECT symbol, shares FROM List_Contains WHERE list_id = %s;"
        cursor.execute(query, (list_id,))
        stocks_in_list = cursor.fetchall()
        total_list_value = 0.0
        if stocks_in_list:
            print("\nStocks in List:")
            for symbol, shares in stocks_in_list:
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
                total_list_value += stock_value
                print(f"- {symbol}: {shares} shares, Share Price: ${close_price:,.2f}, Value: ${stock_value:,.2f}")
        else:
            print("\nNo stocks in this list.")
        
        print(f"\n🏦 Total List Market Value: ${total_list_value:,.2f}")
        print("----------------------------")
        
        # Menu options
        if is_creator:
            print("\n📊 Stock List Menu:")
            print("1. ➕ Add Stock")
            print("2. ➖ Remove Stock")
            print("3. 🔗 Share List")
            print("4. 📈 View Portfolio Stats (Not implemented yet)")
            print("5. ❌ Delete List")
            print("6. 🔙 Go Back")
            choice = input("Choose an option: ")
            if choice == "1":
                add_stock(list_id)
            elif choice == "2":
                remove_stock(list_id)
            elif choice == "3":
                share_list(list_id)
            elif choice == "4":
                print("Option not implemented yet.")
                sleep(1)
            elif choice == "5":
                if delete_list(list_id):
                    # Once deleted, exit the menu.
                    break
            elif choice == "6":
                break
            else:
                print("❌ Invalid option, please try again.")
        else:
            print("\n📊 Stock List Menu:")
            print("1. 📈 View Portfolio Stats (Not implemented yet)")
            print("2. 🔙 Go Back")
            choice = input("Choose an option: ")
            if choice == "1":
                print("Option not implemented yet.")
                sleep(1)
            elif choice == "2":
                break
            else:
                print("❌ Invalid option, please try again.")

def add_stock(list_id):
    symbol = input("Enter the stock symbol to add: ").upper().strip()
    try:
        shares = int(input("Enter the number of shares: "))
        if shares <= 0:
            print("❌ Shares must be a positive integer.")
            return
    except ValueError:
        print("❌ Invalid number of shares.")
        return
    
    # Check if the stock exists
    query = "SELECT symbol FROM Stock WHERE symbol = %s;"
    cursor.execute(query, (symbol,))
    if not cursor.fetchone():
        print("❌ Stock symbol does not exist.")
        return
    
    # Check if the stock is already in the list
    query = "SELECT shares FROM List_Contains WHERE list_id = %s AND symbol = %s;"
    cursor.execute(query, (list_id, symbol))
    result = cursor.fetchone()
    if result:
        new_shares = result[0] + shares
        update_query = "UPDATE List_Contains SET shares = %s WHERE list_id = %s AND symbol = %s;"
        cursor.execute(update_query, (new_shares, list_id, symbol))
    else:
        insert_query = "INSERT INTO List_Contains (list_id, symbol, shares) VALUES (%s, %s, %s);"
        cursor.execute(insert_query, (list_id, symbol, shares))
    conn.commit()
    print(f"✅ Added {shares} shares of {symbol} to the list.")

def remove_stock(list_id):
    symbol = input("Enter the stock symbol to remove: ").upper().strip()
    try:
        shares = int(input("Enter the number of shares to remove: "))
        if shares <= 0:
            print("❌ Shares must be a positive integer.")
            return
    except ValueError:
        print("❌ Invalid number of shares.")
        return
    
    # Check if the stock exists in the list
    query = "SELECT shares FROM List_Contains WHERE list_id = %s AND symbol = %s;"
    cursor.execute(query, (list_id, symbol))
    result = cursor.fetchone()
    if not result:
        print("❌ Stock not found in the list.")
        return
    
    current_shares = result[0]
    if shares > current_shares:
        print("❌ Cannot remove more shares than are in the list.")
        return
    elif shares == current_shares:
        delete_query = "DELETE FROM List_Contains WHERE list_id = %s AND symbol = %s;"
        cursor.execute(delete_query, (list_id, symbol))
    else:
        new_shares = current_shares - shares
        update_query = "UPDATE List_Contains SET shares = %s WHERE list_id = %s AND symbol = %s;"
        cursor.execute(update_query, (new_shares, list_id, symbol))
    conn.commit()
    print(f"✅ Removed {shares} shares of {symbol} from the list.")

def share_list(list_id):
    # Prompt the creator for the friend's username
    friend_username = input("Enter the username of the friend you want to share this list with: ").strip()
    
    # Retrieve friend's user_id from Users table
    query = "SELECT user_id FROM Users WHERE username = %s;"
    cursor.execute(query, (friend_username,))
    friend = cursor.fetchone()
    if not friend:
        print("❌ No user found with that username.")
        return
    friend_user_id = friend[0]
    
    # Check if the friend relationship exists in FRIENDSHIP
    current_user_id = auth.current_user["id"]
    query = """
        SELECT *
        FROM FRIENDSHIP
        WHERE (user_id1 = %s AND user_id2 = %s)
           OR (user_id1 = %s AND user_id2 = %s);
    """
    cursor.execute(query, (current_user_id, friend_user_id, friend_user_id, current_user_id))
    friendship = cursor.fetchone()
    if not friendship:
        print("❌ You are not friends with that user.")
        return
    
    # Check if the list is already shared with that user
    query = "SELECT * FROM List_Shared_With WHERE user_id = %s AND list_id = %s;"
    cursor.execute(query, (friend_user_id, list_id))
    if cursor.fetchone():
        print("❌ This list is already shared with that user.")
        return
    
    # Insert a record into List_Shared_With
    query = "INSERT INTO List_Shared_With (user_id, list_id) VALUES (%s, %s);"
    cursor.execute(query, (friend_user_id, list_id))
    conn.commit()
    print(f"✅ List shared with {friend_username} successfully.")
    
    # Optionally update the list visibility to 'shared' if currently private
    query = "SELECT visibility FROM Stock_List WHERE list_id = %s;"
    cursor.execute(query, (list_id,))
    current_visibility = cursor.fetchone()[0]
    if current_visibility == 'private':
        query = "UPDATE Stock_List SET visibility = 'shared' WHERE list_id = %s;"
        cursor.execute(query, (list_id,))
        conn.commit()
        print("🔒 List visibility updated to 'shared'.")

def delete_list(list_id):
    confirmation = input("Are you sure you want to delete this stock list? All associated data will be removed. This action cannot be undone. (y/n): ")
    if confirmation.lower() == 'y':
        query = "DELETE FROM Stock_List WHERE list_id = %s;"
        cursor.execute(query, (list_id,))
        conn.commit()
        print("✅ Stock list deleted successfully.")
        return True
    else:
        print("Deletion cancelled.")
        return False
