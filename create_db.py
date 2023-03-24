import sqlite3
from contextlib import closing

DB_NAME = "users.db"


def create_db():
    with closing(sqlite3.connect(DB_NAME)) as conn:
        with closing(conn.cursor()) as cursor:
            try:
                # Create operation
                create_users = """CREATE TABLE IF NOT EXISTS users (
              id INTEGER PRIMARY KEY,
              phone_number TEXT NOT NULL,
              is_active INTEGER NOT NULL);
              """
                cursor.execute(create_users)

                create_history = """CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL, 
                history_log TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id));
                """
                cursor.execute(create_history)
                print("Table created!")

            except sqlite3.Error as e:
                # Handle errors
                print(f"Error creating table: {e}")


def insert_command(conn, phone_number, active):
    command = "INSERT INTO users VALUES (?, ?)"
    cur = conn.cursor()
    cur.execute("BEGIN")
    try:
        cur.execute(
            command,
            (
                phone_number,
                active,
            ),
        )
        cur.execute("COMMIT")
    except conn.Error as e:
        print("Got an error: ", e)
        print("Aborting...")
        cur.execute("ROLLBACK")


# Define function to add a new user and its associated history log to the database
def add_new_user(phone_number, history_log):
    with closing(sqlite3.connect(DB_NAME)) as conn:
        with closing(conn.cursor()) as cursor:
            # Add new user to the users table
            cursor.execute(
                "INSERT INTO users (phone_number, is_active) VALUES (?, 0)",
                (phone_number,),
            )
            user_id = cursor.lastrowid

            # Add new history log to the history table
            cursor.execute(
                "INSERT INTO history (user_id, history_log) VALUES (?, ?)",
                (user_id, history_log),
            )

            # Commit changes and close the connection
            conn.commit()


if __name__ == "__main__":
    create_db()
    add_new_user("+16135550166", "User signed up for the app ONE")
    add_new_user("+16135550185", "User signed up for the app TWO")
    add_new_user("+16135550118", "User signed up for the app THREE")
