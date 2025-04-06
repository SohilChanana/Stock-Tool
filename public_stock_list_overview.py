import auth
from db import conn, cursor
from time import sleep
import stock_list_menu

def public_stock_list_menu_view():
    while True:
        public_lists = display_public_lists()
        print("\n📃 Public Stock Lists Menu:")
        if public_lists:
            print("1. 🔍 Open Stock List")
            print("2. 🔙 Go Back")
        else:
            print("1. 🔙 Go Back")
            
        choice = input("Choose an option: ")
        
        if public_lists and choice == "1":
            open_public_stock_list(public_lists)
        elif (not public_lists and choice == "1") or (public_lists and choice == "2"):
            break
        else:
            print("❌ Invalid option, please try again.")

def display_public_lists():
    query = """
        SELECT sl.list_id, sl.name, sl.visibility, u.username, sl.user_id
        FROM Stock_List sl
        JOIN Users u ON sl.user_id = u.user_id
        WHERE sl.visibility = 'public';
    """
    cursor.execute(query)
    public_lists = cursor.fetchall()
    print("\n----------------------------")
    if public_lists:
        print("Public Stock Lists:")
        for list_id, name, visibility, creator_username, creator_id in public_lists:
            print(f"Name: {name}, Created by: {creator_username}")
    else:
        print("\nThere are no public stock lists.")
    print("----------------------------")
    return public_lists

def open_public_stock_list(public_lists):
    # Build a dictionary where the key is the lowercased list name and the value is a list of tuples:
    # (list_id, is_creator, creator_username)
    all_lists = {}
    current_user_id = auth.current_user["id"]
    for lst in public_lists:
        list_id, name, visibility, creator_username, creator_id = lst
        key = name.lower()
        is_creator = (creator_id == current_user_id)
        all_lists.setdefault(key, []).append((list_id, is_creator, creator_username))
    
    name_input = input("Enter the name of the stock list you want to open: ").lower().strip()
    if name_input in all_lists:
        options = all_lists[name_input]
        if len(options) > 1:
            print("Multiple stock lists found with the same name. Please specify the creator:")
            for option in options:
                print(f"Creator: {option[2]}")
            creator_input = input("Enter the creator's username: ").lower().strip()
            chosen = None
            for option in options:
                if option[2].lower() == creator_input:
                    chosen = option
                    break
            if chosen:
                list_id, is_creator, _ = chosen
                stock_list_menu.view_stock_list_menu(list_id, is_creator)
            else:
                print("❌ No matching creator found for that list name.")
                sleep(1)
        else:
            list_id, is_creator, _ = options[0]
            stock_list_menu.view_stock_list_menu(list_id, is_creator)
    else:
        print("❌ Stock list not found. Please check the name and try again.")
        sleep(1)
