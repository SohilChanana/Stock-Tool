import auth
from db import conn, cursor
from time import sleep
import stocks
from ansi_format import style_menu_option, style_input_prompt, style_error, style_success, style_label, style_info

def view_stock_list_menu(list_id, is_creator):
    """
    Displays the stock list menu for a specific stock list.
    If the user is the creator of the list, they have additional options to modify it.
    """
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
            print(style_error("List not found."))
            return
        name, creator, visibility = result
        print(style_label("\n----------------------------"))
        print(style_label(f"📃 Stock List: {name}"))
        print(style_label(f"👤 Created by: {creator}"))
        print(style_label(f"🔒 Visibility: {visibility}"))
        
        # Display stocks in the list and calculate total market value
        query = "SELECT symbol, shares FROM List_Contains WHERE list_id = %s;"
        cursor.execute(query, (list_id,))
        stocks_in_list = cursor.fetchall()
        total_list_value = 0.0
        if stocks_in_list:
            print(style_label("\nStocks in List:"))
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
                print(style_info(f"- {symbol}: {shares} shares, Share Price: ${close_price:,.2f}, Value: ${stock_value:,.2f}"))
        else:
            print(style_info("\nNo stocks in this list."))
        
        print(style_label(f"\n🏦 Total List Market Value: ${total_list_value:,.2f}"))
        print(style_label("----------------------------"))
        
        # Menu options for the list
        if is_creator:
            print(style_label("\n📊 Stock List Menu:"))
            print(style_menu_option("1. ➕ Add Stock"))
            print(style_menu_option("2. ➖ Remove Stock"))
            print(style_menu_option("3. 🔗 Share List"))
            print(style_menu_option("4. 📈 View Stock Stats"))
            print(style_menu_option("5. 📈 View List Stats"))
            print(style_menu_option("6. 💬 Manage Reviews"))
            print(style_menu_option("7. ❌ Delete List"))
            print(style_menu_option("8. 🔙 Go Back"))
            choice = input(style_input_prompt("Choose an option: "))
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
                print(style_error("❌ Invalid option, please try again."))
                sleep(1)
        else:
            print(style_label("\n📊 Stock List Menu:"))
            print(style_menu_option("1. 📈 View Stock Stats"))
            print(style_menu_option("2. 📈 View List Stats"))
            print(style_menu_option("3. 💬 Manage Reviews"))
            print(style_menu_option("4. 🔙 Go Back"))
            choice = input(style_input_prompt("Choose an option: "))
            if choice == "1":
                stocks.view_stock_stats()
            elif choice == "2":
                stocks.view_list_stats(list_id)
            elif choice == "3":
                review_menu(list_id)
            elif choice == "4":
                break
            else:
                print(style_error("❌ Invalid option, please try again."))
                sleep(1)

def add_stock(list_id):
    """
    Adds a stock to the user's stock list.
    """
    symbol = input(style_input_prompt("Enter the stock symbol to add: ")).upper().strip()
    try:
        shares = int(input(style_input_prompt("Enter the number of shares: ")))
        if shares <= 0:
            print(style_error("❌ Shares must be a positive integer."))
            sleep(1)
            return
    except ValueError:
        print(style_error("❌ Invalid number of shares."))
        sleep(1)
        return
    
    # Check if the stock exists
    query = "SELECT symbol FROM Stock WHERE symbol = %s;"
    cursor.execute(query, (symbol,))
    if not cursor.fetchone():
        print(style_error("❌ Stock symbol does not exist."))
        sleep(1)
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
    print(style_success(f"✅ Added {shares} shares of {symbol} to the list."))
    sleep(1)

def remove_stock(list_id):
    """
    Removes a stock from the user's stock list.
    """
    symbol = input(style_input_prompt("Enter the stock symbol to remove: ")).upper().strip()
    try:
        shares = int(input(style_input_prompt("Enter the number of shares to remove: ")))
        if shares <= 0:
            print(style_error("❌ Shares must be a positive integer."))
            sleep(1)
            return
    except ValueError:
        print(style_error("❌ Invalid number of shares."))
        sleep(1)
        return
    
    # Check if the stock exists in the list
    query = "SELECT shares FROM List_Contains WHERE list_id = %s AND symbol = %s;"
    cursor.execute(query, (list_id, symbol))
    result = cursor.fetchone()
    if not result:
        print(style_error("❌ Stock not found in the list."))
        sleep(1)
        return
    
    current_shares = result[0]
    if shares > current_shares:
        print(style_error("❌ Cannot remove more shares than are in the list."))
        sleep(1)
        return
    elif shares == current_shares:
        delete_query = "DELETE FROM List_Contains WHERE list_id = %s AND symbol = %s;"
        cursor.execute(delete_query, (list_id, symbol))
    else:
        new_shares = current_shares - shares
        update_query = "UPDATE List_Contains SET shares = %s WHERE list_id = %s AND symbol = %s;"
        cursor.execute(update_query, (new_shares, list_id, symbol))
    conn.commit()
    print(style_success(f"✅ Removed {shares} shares of {symbol} from the list."))
    sleep(1)

def share_list(list_id):
    """
    Shares the stock list with a friend.
    """
    friend_username = input(style_input_prompt("Enter the username of the friend you want to share this list with: ")).strip()
    
    # Retrieve friend's user_id from Users table
    query = "SELECT user_id FROM Users WHERE username = %s;"
    cursor.execute(query, (friend_username,))
    friend = cursor.fetchone()
    if not friend:
        print(style_error("❌ No user found with that username."))
        sleep(1)
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
        print(style_error("❌ You are not friends with that user."))
        sleep(1)
        return
    
    # Check if the list is already shared with that user
    query = "SELECT * FROM List_Shared_With WHERE user_id = %s AND list_id = %s;"
    cursor.execute(query, (friend_user_id, list_id))
    if cursor.fetchone():
        print(style_error("❌ This list is already shared with that user."))
        sleep(1)
        return
    
    # Insert a record into List_Shared_With
    query = "INSERT INTO List_Shared_With (user_id, list_id) VALUES (%s, %s);"
    cursor.execute(query, (friend_user_id, list_id))
    conn.commit()
    print(style_success(f"✅ List shared with {friend_username} successfully."))
    
    # Update the list visibility to 'shared' if currently private
    query = "SELECT visibility FROM Stock_List WHERE list_id = %s;"
    cursor.execute(query, (list_id,))
    current_visibility = cursor.fetchone()[0]
    if current_visibility.lower() == 'private':
        query = "UPDATE Stock_List SET visibility = 'shared' WHERE list_id = %s;"
        cursor.execute(query, (list_id,))
        conn.commit()
        print(style_label("🔒 List visibility updated to 'shared'."))
    sleep(1)

def delete_list(list_id):
    """
    Deletes the stock list and all associated data.
    """
    confirmation = input(style_input_prompt("Are you sure you want to delete this stock list? All associated data will be removed. This action cannot be undone. (y/n): "))
    if confirmation.lower() == 'y':
        query = "DELETE FROM Stock_List WHERE list_id = %s;"
        cursor.execute(query, (list_id,))
        conn.commit()
        print(style_success("✅ Stock list deleted successfully."))
        sleep(1)
        return True
    else:
        print(style_error("❌ Deletion cancelled."))
        sleep(1)
        return False


################# Review Functionality ##############################

def review_menu(list_id):
    """
    Displays a sub-menu for managing reviews with emoji-enhanced options.
    """
    while True:
        print(style_label("\n📝 Review Menu:"))
        print(style_menu_option("1. 🖊️  Add/Update Review"))
        print(style_menu_option("2. 👀 View Reviews"))
        print(style_menu_option("3. 🗑️  Delete Review"))
        print(style_menu_option("4. 🔙 Go Back"))
        choice = input(style_input_prompt("Enter your choice: ")).strip()
        
        if choice == "1":
            add_update_review(list_id)
        elif choice == "2":
            view_reviews(list_id)
        elif choice == "3":
            delete_review(list_id)
        elif choice == "4":
            break
        else:
            print(style_error("❌ Invalid choice. Please try again."))
            sleep(1)


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
            confirm = input(style_input_prompt("⚠️ A review already exists for this stock list. This will overwrite your previous review. Are you sure? (y/n): ")).strip()
            if confirm.lower() != 'y':
                print(style_error("❌ Operation cancelled."))
                sleep(1)
                return

        review_text = input(style_input_prompt("Enter your review (max 4000 characters): ")).strip()
        if not review_text:
            print(style_error("❌ Review cannot be empty. Operation cancelled."))
            sleep(1)
            return
        if len(review_text) > 4000:
            print(style_error("❌ Review exceeds maximum length. Operation cancelled."))
            sleep(1)
            return

        if existing_review:
            review_id = existing_review[0]
            cur.execute(
                "UPDATE Review SET review_text = %s, review_date = CURRENT_TIMESTAMP WHERE review_id = %s",
                (review_text, review_id)
            )
            print(style_success("✅ Review updated successfully."))
            sleep(1)
        else:
            cur.execute(
                "INSERT INTO Review (review_text, review_date, stock_list_id, user_id) VALUES (%s, CURRENT_TIMESTAMP, %s, %s)",
                (review_text, stock_list_id, auth.current_user["id"])
            )
            print(style_success("✅ Review added successfully."))
            sleep(1)
    conn.commit()


def view_reviews(stock_list_id):
    """
    Displays all reviews for the specified stock list.
    Reviews are shown only if the list is public or the user is the owner.
    """
    with conn.cursor() as cur:
        # Retrieve stock list details: name, owner, and visibility.
        cur.execute(
            "SELECT name, user_id, visibility FROM Stock_List WHERE list_id = %s",
            (stock_list_id,)
        )
        stock_list = cur.fetchone()
        if not stock_list:
            print(style_error("❌ Stock list not found."))
            sleep(1)
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
            print(style_error("❌ No reviews available for this stock list."))
            sleep(1)
        else:
            print(style_label(f"\n--- Reviews for Stock List: {list_name} ---"))
            for review in reviews:
                username, review_text, review_date = review
                print(style_label("\n----------------------------"))
                print(style_label(f"Review by: {username} on {review_date}"))
                print(style_info(f"Review: {review_text}"))
                print(style_label("----------------------------"))


def delete_review(stock_list_id):
    """
    Deletes a review from the stock list.
    """
    with conn.cursor() as cur:
        # Get the stock list owner's user ID.
        cur.execute("SELECT user_id FROM Stock_List WHERE list_id = %s", (stock_list_id,))
        stock_list = cur.fetchone()
        if not stock_list:
            print(style_error("❌ Stock list not found."))
            sleep(1)
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
                print(style_error("❌ No reviews to delete."))
                sleep(1)
                return
            print(style_label("\nReviews:"))
            for review in reviews:
                print(style_info(f"Reviewer: {review[1]}"))
            review_username = input(style_input_prompt("Enter the username whose review you want to delete: ")).strip()
            if not review_username:
                print(style_error("❌ Invalid username. Operation cancelled."))
                sleep(1)
                return
            review_to_delete = None
            for review in reviews:
                if review[1].lower() == review_username.lower():
                    review_to_delete = review[0]
                    break
            if review_to_delete is None:
                print(style_error(f"❌ No review found for username '{review_username}'."))
                sleep(1)
                return
            cur.execute("DELETE FROM Review WHERE review_id = %s", (review_to_delete,))
            print(style_success("✅ Review deleted successfully."))
            sleep(1)
        else:
            cur.execute("SELECT review_id FROM Review WHERE stock_list_id = %s AND user_id = %s", 
                        (stock_list_id, auth.current_user["id"]))
            row = cur.fetchone()
            if not row:
                print(style_error("❌ You do not have a review to delete for this stock list."))
                sleep(1)
                return
            confirm = input(style_input_prompt("Are you sure you want to delete your review? (y/n): ")).strip()
            if confirm.lower() != 'y':
                print(style_error("❌ Operation cancelled."))
                sleep(1)
                return
            cur.execute("DELETE FROM Review WHERE review_id = %s", (row[0],))
            print(style_success("✅ Your review has been deleted."))
            sleep(1)
    conn.commit()
