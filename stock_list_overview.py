import auth
from db import conn, cursor
from time import sleep
import stock_list_menu
from ansi_format import style_menu_option, style_input_prompt, style_error, style_success, style_label, style_info

def stock_list_menu_view():
    """
    Stock list menu function that allows users to create and view their stock lists.
    """
    while True:
        owned_lists = display_owned_lists()
        shared_lists = display_shared_lists()
        
        print(style_label("\n📃 Stock Lists Menu:"))
        print(style_menu_option("1. 🆕 Create Stock List"))
        if owned_lists or shared_lists:
            print(style_menu_option("2. 🔍 Open Stock List"))
            print(style_menu_option("3. 🔙 Go Back"))
        else:
            print(style_menu_option("2. 🔙 Go Back"))
            
        choice = input(style_input_prompt("Choose an option: "))
        
        if choice == "1":
            create_stock_list()
        elif choice == "2" and (owned_lists or shared_lists):
            open_stock_list(owned_lists, shared_lists)
        elif (choice == "2" and not (owned_lists or shared_lists)) or (choice == "3" and (owned_lists or shared_lists)):
            break
        else:
            print(style_error("❌ Invalid option, please try again."))
            sleep(1)

def display_owned_lists():
    """
    Display all stock lists owned by the current user.
    """
    user_id = auth.current_user["id"]
    query = """
    SELECT sl.list_id, sl.name, sl.visibility, u.username
    FROM Stock_List sl
    JOIN Users u ON sl.user_id = u.user_id
    WHERE sl.user_id = %s;
    """
    cursor.execute(query, (user_id,))
    owned_lists = cursor.fetchall()
    print(style_label("\n----------------------------"))
    if owned_lists:
        print(style_label("Your Stock Lists:"))
        for list_id, name, visibility, username in owned_lists:
            print(style_info(f"Name: {name}, Visibility: {visibility}, Created by: {username}"))
    else:
        print(style_info("\nYou have no stock lists."))
    
    return owned_lists

def display_shared_lists():
    """
    Display all stock lists shared with the current user.
    """
    user_id = auth.current_user["id"]
    query = """
    SELECT sl.list_id, sl.name, sl.visibility, u.username
    FROM List_Shared_With lsw
    JOIN Stock_List sl ON lsw.list_id = sl.list_id
    JOIN Users u ON sl.user_id = u.user_id
    WHERE lsw.user_id = %s;
    """
    cursor.execute(query, (user_id,))
    shared_lists = cursor.fetchall()
    if shared_lists:
        print(style_label("\nStock Lists Shared With You:"))
        for list_id, name, visibility, username in shared_lists:
            print(style_info(f"Name: {name}, Visibility: {visibility}, Created by: {username}"))
    print(style_label("----------------------------"))
    return shared_lists

def create_stock_list():
    """
    Create a new stock list for the current user.
    """
    user_id = auth.current_user["id"]
    name = input(style_input_prompt("Enter a name for your new stock list: "))
    
    # Check if a stock list with the same name already exists for this user
    query = "SELECT list_id FROM Stock_List WHERE user_id = %s AND name = %s;"
    cursor.execute(query, (user_id, name))
    if cursor.fetchone():
        print(style_error("❌ You already have a stock list with that name. Please choose a different name."))
        sleep(1)
        return
    
    # Ask for visibility: private or public (shared is not an option during creation)
    visibility = input(style_input_prompt("Should this list be private or public? ")).lower().strip()
    if visibility not in ["private", "public"]:
        print(style_error("❌ Invalid visibility option. Please choose either 'private' or 'public'."))
        sleep(1)
        return
    
    query = "INSERT INTO Stock_List (user_id, name, visibility) VALUES (%s, %s, %s) RETURNING list_id;"
    cursor.execute(query, (user_id, name, visibility))
    list_id = cursor.fetchone()[0]
    conn.commit()
    print(style_success(f"✅ Stock list '{name}' created successfully."))
    sleep(1)

def open_stock_list(owned_lists, shared_lists):
    """
    Open a stock list based on user input.
    If multiple lists have the same name, prompt the user to specify the creator.
    """
    all_lists = {}
    for lst in owned_lists:
        key = lst[1].lower()
        all_lists.setdefault(key, []).append((lst[0], True, lst[3]))
    for lst in shared_lists:
        key = lst[1].lower()
        all_lists.setdefault(key, []).append((lst[0], False, lst[3]))
    
    name = input(style_input_prompt("Enter the name of the stock list you want to open: ")).lower().strip()
    if name in all_lists:
        options = all_lists[name]
        if len(options) > 1:
            print(style_label("Multiple stock lists found with the same name. Please specify the creator:"))
            for option in options:
                print(style_info(f"Creator: {option[2]}"))
            creator_input = input(style_input_prompt("Enter the creator's username: ")).lower().strip()
            chosen = None
            for option in options:
                if option[2].lower() == creator_input:
                    chosen = option
                    break
            if chosen:
                list_id, is_creator, _ = chosen
                stock_list_menu.view_stock_list_menu(list_id, is_creator)
            else:
                print(style_error("❌ No matching creator found for that list name."))
                sleep(1)
        else:
            list_id, is_creator, _ = options[0]
            stock_list_menu.view_stock_list_menu(list_id, is_creator)
    else:
        print(style_error("❌ Stock list not found. Please check the name and try again."))
        sleep(1)
