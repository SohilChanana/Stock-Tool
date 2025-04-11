from time import sleep
import pwinput
from ansi_format import style_input_prompt, style_error, style_success, style_info

current_user = {"id": None, "username": None}

def signup(conn, cursor):
    """Sign up a new user and store their session."""
    username = input(style_input_prompt("Enter username: "))
    password = pwinput.pwinput(prompt=style_input_prompt("Enter password: "), mask='●')

    # Check if the username is already taken
    cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
    existing_user = cursor.fetchone()
    if existing_user:
        print(style_error("❌ Error: Username already taken. Please choose a different username."))
        sleep(1)
        return

    try:
        cursor.execute(
            "INSERT INTO users (username, password, registration_date) VALUES (%s, %s, NOW()) RETURNING user_id",
            (username, password)
        )
        user_id = cursor.fetchone()[0]
        conn.commit()
        print(style_success("✅ Signup successful!"))
        sleep(1)

        current_user["id"] = user_id
        current_user["username"] = username
        print(style_info(f"🔹 You are now signed in as {username}"))
        sleep(1)

    except Exception as e:
        print(style_error(f"❌ Error: {e}"))

def login(conn, cursor):
    """Log in an existing user and store their session."""
    username = input(style_input_prompt("Enter username: "))
    password = pwinput.pwinput(prompt=style_input_prompt("Enter password: "), mask='●')

    try:
        cursor.execute("SELECT user_id, password FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user and password == user[1]:
            current_user["id"] = user[0]
            current_user["username"] = username
            print(style_success(f"\n✅ Login successful! 👋 Welcome, {username}"))
            sleep(1)
        else:
            print(style_error("❌ Invalid username or password."))
            sleep(1)

    except Exception as e:
        print(style_error(f"❌ Error: {e}"))

def logout():
    """Log out the current user."""
    current_user["id"] = None
    current_user["username"] = None
    print(style_info("🔓 You have been logged out."))
    sleep(1)
