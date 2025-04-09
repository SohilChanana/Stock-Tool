import auth
from db import conn, cursor
from time import sleep
import stocks

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
            print("4. 📈 View Stock Stats")
            print("5. 📈 View List Stats")
            print("6. 💬 Manage Reviews")
            print("7. ❌ Delete List")
            print("8. 🔙 Go Back")
            choice = input("Choose an option: ")
            if choice == "1":
                add_stock(list_id)
            elif choice == "2":
                remove_stock(list_id)
            elif choice == "3":
                share_list(list_id)
            elif choice == "4":
                stocks.view_stock_stats()
            elif choice == "5":
                stocks.view_list_stats(list_id)
            elif choice == "6":
                review_menu(list_id)
            elif choice == "7":
                if delete_list(list_id):
                    break
            elif choice == "8":
                break
            else:
                print("❌ Invalid option, please try again.")
                sleep(1)
        else:
            print("\n📊 Stock List Menu:")
            print("1. 📈 View Stock Stats")
            print("2. 📈 View List Stats")
            print("3. 💬 Manage Reviews")
            print("4. 🔙 Go Back")
            choice = input("Choose an option: ")
            if choice == "1":
                stocks.view_stock_stats()
            elif choice == "2":
                stocks.view_list_stats(list_id)
            elif choice == "3":
                review_menu(list_id)
            elif choice == "4":
                break
            else:
                print("❌ Invalid option, please try again.")
                sleep(1)

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


################# Review Functionality ##############################

def review_menu(list_id):
    """
    Displays a sub-menu for managing reviews with emoji-enhanced options.
    """
    while True:
        print("\n📝 Review Menu:")
        print("1. 🖊️  Add/Update Review")
        print("2. 👀 View Reviews")
        print("3. 🗑️  Delete Review")
        print("4. 🔙 Go Back")
        choice = input("Enter your choice: ").strip()
        
        if choice == "1":
            add_update_review(list_id)
        elif choice == "2":
            view_reviews(list_id)
        elif choice == "3":
            delete_review(list_id)
        elif choice == "4":
            break
        else:
            print("❌ Invalid choice. Please try again.")


def add_update_review(stock_list_id):
    """
    Adds a new review or updates an existing one for the stock list.
    If a review exists, prompts for confirmation to overwrite.
    """
    with conn.cursor() as cur:
        # Check if a review already exists for this user and stock list.
        cur.execute(
            "SELECT review_id FROM Review WHERE stock_list_id = %s AND user_id = %s",
            (stock_list_id, auth.current_user["id"])
        )
        existing_review = cur.fetchone()
        
        if existing_review:
            print("❌ A review already exists for this stock list.")
            confirm = input("This will overwrite your previous review. Are you sure? (y/n): ").strip()
            if confirm.lower() != 'y':
                print("❌ Operation cancelled.")
                return

        review_text = input("Enter your review (max 4000 characters): ").strip()
        if not review_text:
            print("❌ Review cannot be empty. Operation cancelled.")
            return
        if len(review_text) > 4000:
            print("❌ Review exceeds maximum length. Operation cancelled.")
            return

        if existing_review:
            review_id = existing_review[0]
            cur.execute(
                "UPDATE Review SET review_text = %s, review_date = CURRENT_TIMESTAMP WHERE review_id = %s",
                (review_text, review_id)
            )
            print("✅ Review updated successfully.")
        else:
            cur.execute(
                "INSERT INTO Review (review_text, review_date, stock_list_id, user_id) VALUES (%s, CURRENT_TIMESTAMP, %s, %s)",
                (review_text, stock_list_id, auth.current_user["id"])
            )
            print("✅ Review added successfully.")
    conn.commit()


def view_reviews(stock_list_id):
    """
    Retrieves and displays reviews for the given stock list.
    For public lists or if the current user is the list owner, all reviews are shown.
    For non-public lists, only the current user's review is shown.
    
    The function displays:
      - The stock list name,
      - The current user (for reference),
      - For each review: the reviewer's username, the review date, and the review text.
    """
    with conn.cursor() as cur:
        # Retrieve stock list details: name, owner, and visibility.
        cur.execute(
            "SELECT name, user_id, visibility FROM Stock_List WHERE list_id = %s",
            (stock_list_id,)
        )
        stock_list = cur.fetchone()
        if not stock_list:
            print("❌ Stock list not found.")
            return

        list_name, owner_id, visibility = stock_list

        if visibility.lower() == 'public' or auth.current_user["id"] == owner_id:
            query = """
                SELECT u.username, r.review_text, r.review_date 
                FROM Review r 
                JOIN Users u ON r.user_id = u.user_id
                WHERE r.stock_list_id = %s
            """
            cur.execute(query, (stock_list_id,))
        else:
            query = """
                SELECT u.username, r.review_text, r.review_date 
                FROM Review r 
                JOIN Users u ON r.user_id = u.user_id
                WHERE r.stock_list_id = %s AND r.user_id = %s
            """
            cur.execute(query, (stock_list_id, auth.current_user["id"]))

        reviews = cur.fetchall()

        if not reviews:
            print("❌ No reviews available for this stock list.")
        else:
            print(f"\n--- Reviews for Stock List: {list_name} ---")
            for review in reviews:
                username, review_text, review_date = review
                print("\n----------------------------")
                print(f"Review by: {username} on {review_date}")
                print(f"Review: {review_text}")
                print("----------------------------")


def delete_review(stock_list_id):
    """
    Deletes a review from the stock list.
    The stock list owner can delete any review, while non-owners may only delete their own review.
    For owners, the function now asks for the username of the reviewer instead of the review ID.
    """
    with conn.cursor() as cur:
        # Get the stock list owner's user ID.
        cur.execute("SELECT user_id FROM Stock_List WHERE list_id = %s", (stock_list_id,))
        stock_list = cur.fetchone()
        if not stock_list:
            print("❌ Stock list not found.")
            return
        
        owner_id = stock_list[0]
        
        if auth.current_user["id"] == owner_id:
            # For the list owner, list all reviews with reviewer names.
            query = """
                SELECT r.review_id, u.username
                FROM Review r 
                JOIN Users u ON r.user_id = u.user_id
                WHERE r.stock_list_id = %s
            """
            cur.execute(query, (stock_list_id,))
            reviews = cur.fetchall()
            if not reviews:
                print("❌ No reviews to delete.")
                return
            print("\nReviews:")
            for review in reviews:
                print(f"Reviewer: {review[1]}")
            review_username = input("Enter the username whose review you want to delete: ").strip()
            if not review_username:
                print("❌ Invalid username. Operation cancelled.")
                return
            # Identify the review_id corresponding to the given username (assuming one review per user).
            review_to_delete = None
            for review in reviews:
                if review[1].lower() == review_username.lower():
                    review_to_delete = review[0]
                    break
            if review_to_delete is None:
                print(f"❌ No review found for username '{review_username}'.")
                return
            cur.execute("DELETE FROM Review WHERE review_id = %s", (review_to_delete,))
            print("✅ Review deleted successfully.")
        else:
            cur.execute("SELECT review_id FROM Review WHERE stock_list_id = %s AND user_id = %s", 
                        (stock_list_id, auth.current_user["id"]))
            row = cur.fetchone()
            if not row:
                print("❌ You do not have a review to delete for this stock list.")
                return
            confirm = input("Are you sure you want to delete your review? (y/n): ").strip()
            if confirm.lower() != 'y':
                print("❌ Operation cancelled.")
                return
            cur.execute("DELETE FROM Review WHERE review_id = %s", (row[0],))
            print("✅ Your review has been deleted.")
    conn.commit()