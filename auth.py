current_user = {
    "id": None,
    "username": None
}

def signup(conn, cursor):
    """Sign up a new user and store their session."""
    username = input("Enter username: ")
    password = input("Enter password: ")

    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s) RETURNING user_id",
                       (username, password))
        user_id = cursor.fetchone()[0]  # Get the newly created user's ID
        conn.commit()
        print("✅ Signup successful!")

        # Store user session
        current_user["id"] = user_id
        current_user["username"] = username
        print(f"🔹 You are now signed in as {username}")

    except Exception as e:
        print(f"❌ Error: {e}")

def login(conn, cursor):
    """Log in an existing user and store their session."""
    username = input("Enter username: ")
    password = input("Enter password: ")

    try:
        
        cursor.execute("SELECT user_id, password FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user and password == user[1]:  # Compare plain text passwords
            current_user["id"] = user[0]  # Save user ID
            current_user["username"] = username  # Save username
            print(f"✅ Login successful! Welcome, {username}")
        else:
            print("❌ Invalid username or password.")

    except Exception as e:
        print(f"❌ Error: {e}")