from time import sleep
current_user = {"id": None, "username": None}

def signup(conn, cursor):
    """Sign up a new user and store their session."""
    username = input("Enter username: ")
    password = input("Enter password: ")

    # Check if the username is already taken
    cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
    existing_user = cursor.fetchone()
    if existing_user:
        print("❌ Error: Username already taken. Please choose a different username.")
        sleep(1)
        return

    try:
        cursor.execute(
            "INSERT INTO users (username, password, registration_date) VALUES (%s, %s, NOW()) RETURNING user_id",
            (username, password)
        )
        user_id = cursor.fetchone()[0]
        conn.commit()
        print("✅ Signup successful!")
        sleep(1)

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

        if user and password == user[1]:
            current_user["id"] = user[0]
            current_user["username"] = username
            print(f"\n✅ Login successful! 👋 Welcome, {username}")
            sleep(1)
        else:
            print("❌ Invalid username or password.")
            sleep(1)

    except Exception as e:
        print(f"❌ Error: {e}")

def logout():
    """Log out the current user."""
    current_user["id"] = None
    current_user["username"] = None
    print("🔓 You have been logged out.")
    sleep(1)
