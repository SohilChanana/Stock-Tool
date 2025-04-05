import auth
from db import conn, cursor
from datetime import datetime, timedelta

def send_friend_request(from_username, to_username):
    if from_username == to_username:
        print("❌ You cannot send a friend request to yourself.")
        return

    # Get the target user
    cursor.execute("SELECT user_id FROM users WHERE username = %s", (to_username,))
    to_user = cursor.fetchone()
    if not to_user:
        print("❌ User not found.")
        return

    cursor.execute("SELECT user_id FROM users WHERE username = %s", (from_username,))
    from_user = cursor.fetchone()

    # Check if they are already friends
    cursor.execute("""
        SELECT * FROM FRIENDSHIP
        WHERE (user_id1 = %s AND user_id2 = %s) OR (user_id1 = %s AND user_id2 = %s)
    """, (from_user[0], to_user[0], to_user[0], from_user[0]))
    friendship = cursor.fetchone()
    if friendship:
        print("❌ You are already friends with this user.")
        return

    # Check for an existing friend request
    cursor.execute("""
        SELECT status, last_updated FROM FRIEND_REQUEST
        WHERE from_user_id = %s AND to_user_id = %s
    """, (from_user[0], to_user[0]))
    existing_request = cursor.fetchone()

    if existing_request:
        status, last_updated = existing_request
        if status == 'pending':
            print("❌ Friend request already sent.")
            return
        elif status == 'rejected' and datetime.now() - last_updated < timedelta(minutes=5):
            print("❌ You must wait 5 minutes before resending a request.")
            return

    cursor.execute("""
        INSERT INTO FRIEND_REQUEST (from_user_id, to_user_id, request_date, status, last_updated)
        VALUES (%s, %s, NOW(), 'pending', NOW())
    """, (from_user[0], to_user[0]))
    conn.commit()
    print("✅ Friend request sent!")

def view_and_manage_requests(username):
    cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    if not user:
        print("❌ User not found.")
        return

    user_id = user[0]

    # Fetch incoming pending requests
    cursor.execute("""
        SELECT u.username, fr.status, fr.request_date
        FROM FRIEND_REQUEST fr
        JOIN users u ON fr.from_user_id = u.user_id
        WHERE fr.to_user_id = %s AND fr.status = 'pending'
    """, (user_id,))
    incoming_requests = cursor.fetchall()

    # Fetch outgoing pending requests
    cursor.execute("""
        SELECT u.username, fr.status, fr.request_date
        FROM FRIEND_REQUEST fr
        JOIN users u ON fr.to_user_id = u.user_id
        WHERE fr.from_user_id = %s AND fr.status = 'pending'
    """, (user_id,))
    outgoing_requests = cursor.fetchall()

    print("\n📥 Incoming Friend Requests:")
    if incoming_requests:
        for idx, req in enumerate(incoming_requests, start=1):
            print(f"{idx}. 👤 {req[0]} (Sent: {req[2]})")
    else:
        print("   You have no incoming friend requests.")

    print("\n📤 Outgoing Friend Requests:")
    if outgoing_requests:
        for idx, req in enumerate(outgoing_requests, start=1):
            print(f"{idx}. 👤 {req[0]} (Sent: {req[2]})")
    else:
        print("   You have no outgoing friend requests.")

    # Display a sub-menu with number options and emojis
    print("\n📋 Friend Request Options:")
    print("1. ✅ Manage an Incoming Request")
    print("2. 🔙 Back to Friends Menu")
    choice = input("Choose an option: ").strip()

    if choice == "1":
        if not incoming_requests:
            print("❌ No incoming friend requests to manage.")
            return
        sender_username = input("Enter the username of the friend request to manage: ").strip()
        if not any(req[0] == sender_username for req in incoming_requests):
            print("❌ No incoming friend request from that user.")
            return
        print(f"\nWhat do you want to do with the request from {sender_username}?")
        print("1. ✅ Accept")
        print("2. ❌ Reject")
        print("3. 🔙 Cancel")
        decision = input("Choose an option: ").strip()
        if decision == "1":
            process_friend_request(username, sender_username, 'accept')
        elif decision == "2":
            process_friend_request(username, sender_username, 'reject')
        elif decision == "3":
            return
        else:
            print("❌ Invalid option.")
    elif choice == "2":
        return
    else:
        print("❌ Invalid option.")

def process_friend_request(username, from_username, action):
    # Fetch user_id of the recipient
    cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
    to_user = cursor.fetchone()
    
    if not to_user:
        print("❌ User not found.")
        return
    
    # Fetch user_id of the sender
    cursor.execute("SELECT user_id FROM users WHERE username = %s", (from_username,))
    from_user = cursor.fetchone()
    
    if not from_user:
        print("❌ Request sender not found.")
        return

    # Check if there is a pending request
    cursor.execute("""
        SELECT request_id FROM FRIEND_REQUEST
        WHERE from_user_id = %s AND to_user_id = %s AND status = 'pending'
    """, (from_user[0], to_user[0]))
    request = cursor.fetchone()
    
    if not request:
        print("❌ No pending request from this user.")
        return
    
    # Process the request
    if action == 'accept':
        cursor.execute("""
            INSERT INTO FRIENDSHIP (user_id1, user_id2, friend_since)
            VALUES (%s, %s, NOW())
        """, (from_user[0], to_user[0]))
        cursor.execute("UPDATE FRIEND_REQUEST SET status = 'accepted', last_updated = NOW() WHERE request_id = %s", (request[0],))
        print("✅ Friend request accepted!")
    elif action == 'reject':
        cursor.execute("UPDATE FRIEND_REQUEST SET status = 'rejected', last_updated = NOW() WHERE request_id = %s", (request[0],))
        print("❌ Friend request rejected!")
    
    conn.commit()

def view_friends(username):
    cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
    result = cursor.fetchone()
    if not result:
        print("❌ User not found.")
        return []
    user_id = result[0]
    
    cursor.execute("""
        SELECT u.username, f.friend_since
        FROM FRIENDSHIP f
        JOIN users u ON (f.user_id1 = u.user_id OR f.user_id2 = u.user_id)
        WHERE (f.user_id1 = %s OR f.user_id2 = %s) AND u.user_id != %s
    """, (user_id, user_id, user_id))
    friends = cursor.fetchall()
    
    print("\n👥 Your Friends:")
    if not friends:
        print("   You have no friends added yet.")
    else:
        for friend in friends:
            print(f"- {friend[0]}")
    return friends

def delete_friend(username, friend_username):
    # Fetch user_id of the current user
    cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    
    if not user:
        print("❌ User not found.")
        return
    
    # Fetch user_id of the friend to delete
    cursor.execute("SELECT user_id FROM users WHERE username = %s", (friend_username,))
    friend = cursor.fetchone()
    
    if not friend:
        print("❌ Friend not found.")
        return

    user_id, friend_id = user[0], friend[0]

    # Check if they are actually friends
    cursor.execute("""
        SELECT * FROM FRIENDSHIP
        WHERE (user_id1 = %s AND user_id2 = %s) OR (user_id1 = %s AND user_id2 = %s)
    """, (user_id, friend_id, friend_id, user_id))
    friendship = cursor.fetchone()

    if not friendship:
        print("❌ You are not friends with this user.")
        return

    # Delete friendship record
    cursor.execute("""
        DELETE FROM FRIENDSHIP
        WHERE (user_id1 = %s AND user_id2 = %s) OR (user_id1 = %s AND user_id2 = %s)
    """, (user_id, friend_id, friend_id, user_id))
    conn.commit()

    print("✅ Friend deleted successfully.")

def friends_menu(username):
    while True:
        # Get user_id for summary info
        cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        if not user:
            print("❌ User not found.")
            return
        user_id = user[0]

        # Count pending incoming and outgoing friend requests
        cursor.execute("SELECT COUNT(*) FROM FRIEND_REQUEST WHERE to_user_id = %s AND status = 'pending'", (user_id,))
        incoming_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM FRIEND_REQUEST WHERE from_user_id = %s AND status = 'pending'", (user_id,))
        outgoing_count = cursor.fetchone()[0]

        # Display summary: friends list and counts
        print("\n----------------------------")
        print("Friends Summary:")
        view_friends(username)
        print(f"\nYou have {incoming_count} incoming friend request(s) and {outgoing_count} outgoing friend request(s).")
        print("----------------------------")

        # Display menu options
        print("\n🤝 Friends Menu:")
        print("1. ➕ Send Friend Request")
        print("2. 📥 View/Manage Friend Requests")
        print("3. ❌ Delete a Friend")
        print("4. 🔙 Back to Main Menu")
        choice = input("Choose an option: ").strip()
        
        if choice == "1":
            to_username = input("Enter the username of the person you want to add: ").strip()
            send_friend_request(username, to_username)
        elif choice == "2":
            view_and_manage_requests(username)
        elif choice == "3":
            friend_username = input("Enter the username of the friend to delete: ").strip()
            delete_friend(username, friend_username)
        elif choice == "4":
            break
        else:
            print("❌ Invalid option, try again.")
