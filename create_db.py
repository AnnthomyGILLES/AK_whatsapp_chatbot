import sqlite3

db_name = "users.db"
conn = sqlite3.connect(db_name)


def create_db():
    try:
        cursor = conn.cursor()
        print("Database created!")

        # Create operation
        create_query = """CREATE TABLE IF NOT EXISTS users(
      id INTEGER PRIMARY KEY,
      phone_number TEXT NOT NULL,
      active INTEGER NOT NULL, 
      history_log TEXT);
      """
        cursor.execute(create_query)
        print("Table created!")

    except sqlite3.Error as e:
        # Handle errors
        print(f"Error creating table: {e}")

    finally:
        # Close the connection
        conn.close()


def insert_command(conn, phone_number, active, history_log):
    command = "INSERT INTO student VALUES (?, ?, ?)"
    cur = conn.cursor()
    cur.execute("BEGIN")
    try:
        cur.execute(
            command,
            (
                phone_number,
                active,
                history_log,
            ),
        )
        cur.execute("COMMIT")
    except conn.Error as e:
        print("Got an error: ", e)
        print("Aborting...")
        cur.execute("ROLLBACK")


if __name__ == "__main__":
    create_db()
