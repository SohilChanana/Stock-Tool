import auth
from db import conn, cursor
from datetime import datetime, timedelta

def send_friend_request(from_username, to_username):
    if from_username == to_username:
        print("❌ You cannot send a friend request to yourself.")
        return
    
    cursor.execute("SELECT user_id FROM users WHERE username = %s", (to_username,))
    to_user = cursor.fetchone()
    if not to_user:
        print("❌ User not found.")
        return
    
    cursor.execute("SELECT user_id FROM users WHERE username = %s", (from_username,))
    from_user = cursor.fetchone()
    
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
        elif status in ['rejected', 'accepted'] and datetime.now() - last_updated < timedelta(minutes=5):
            print("❌ You must wait 5 minutes before resending a request.")
            return
    
    cursor.execute("""
        INSERT INTO FRIEND_REQUEST (from_user_id, to_user_id, request_date, status, last_updated)
        VALUES (%s, %s, NOW(), 'pending', NOW())
    """, (from_user[0], to_user[0]))
    conn.commit()
    print("✅ Friend request sent!")

def view_friend_requests(username):
    cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    if not user:
        print("helloworld :)")
        print("❌ User not found.")
        return

    print("apple")

    user_id = user[0]
    
    cursor.execute("""
        SELECT u.username, fr.status, fr.request_date
        FROM FRIEND_REQUEST fr
        JOIN users u ON fr.from_user_id = u.user_id
        WHERE fr.to_user_id = %s AND fr.status = 'pending'
    """, (user_id,))
    incoming_requests = cursor.fetchall()
    
    cursor.execute("""
        SELECT u.username, fr.status, fr.request_date
        FROM FRIEND_REQUEST fr
        JOIN users u ON fr.to_user_id = u.user_id
        WHERE fr.from_user_id = %s AND fr.status = 'pending'
    """, (user_id,))
    outgoing_requests = cursor.fetchall()
    
    print("\n📥 Incoming Friend Requests:")
    for req in incoming_requests:
        print(f"- {req[0]} (Sent: {req[2]})")
    
    print("\n📤 Outgoing Friend Requests:")
    for req in outgoing_requests:
        print(f"- {req[0]} (Sent: {req[2]})")

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
    user_id = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT u.username, f.friend_since
        FROM FRIENDSHIP f
        JOIN users u ON (f.user_id1 = u.user_id OR f.user_id2 = u.user_id)
        WHERE (f.user_id1 = %s OR f.user_id2 = %s) AND u.user_id != %s
    """, (user_id, user_id, user_id))
    friends = cursor.fetchall()
    
    print("\n👥 Your Friends:")
    for friend in friends:
        print(f"- {friend[0]} (Since: {friend[1]})")

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
        print("\n🤝 Friends Menu:")
        print("1. ➕ Send Friend Request")
        print("2. 📥 View Friend Requests")
        print("3. ✅ Accept/Reject Friend Request")
        print("4. 👥 View Friends List")
        print("5. ❌ Delete a Friend")
        print("6. 🔙 Back to Main Menu")
        choice = input("Choose an option: ")
        
        if choice == "1":
            to_username = input("Enter the username of the person you want to add: ")
            send_friend_request(username, to_username)
        elif choice == "2":
            view_friend_requests(username)
        elif choice == "3":
            from_username = input("Enter the username of the sender: ")
            action = input("Accept or Reject? (accept/reject): ").strip().lower()
            process_friend_request(username, from_username, action)
        elif choice == "4":
            view_friends(username)
        elif choice == "5":
            friend_username = input("Enter the username of the friend to delete: ")
            delete_friend(username, friend_username)
        elif choice == "6":
            break
        else:
            print("❌ Invalid option, try again.")
