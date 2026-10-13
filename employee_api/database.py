# ─────────────────────────────────────────────────────────────
# database.py
# ─────────────────────────────────────────────────────────────
# Responsibility:
#   This file has ONE job: give the rest of the application a
#   working MySQL connection whenever it is needed.
#
#   No SQL queries live here.  No API routes live here.
#   It is purely a "connection factory".
#
# Why a separate file?
#   If we ever change databases (e.g., from MySQL to PostgreSQL)
#   we only touch THIS file.  Nothing else changes.
# ─────────────────────────────────────────────────────────────

import os                          # Built-in module to read environment variables
import mysql.connector             # MySQL driver installed via requirements.txt
from mysql.connector import Error  # The specific exception class for MySQL errors
from dotenv import load_dotenv     # Reads our .env file into os.environ

# ── Load the .env file ────────────────────────────────────────
# load_dotenv() searches for a file named ".env" in the current
# directory (or any parent directory) and loads every KEY=VALUE
# pair into os.environ.  After this line, os.getenv("DB_HOST")
# returns "localhost" (or whatever you set in .env).
load_dotenv()


# ── get_connection() ─────────────────────────────────────────
# This function creates and returns a brand-new MySQL connection.
#
# We call it a "connection factory" because every time it is
# called, it builds a fresh connection object.
#
# Returns:
#   mysql.connector.connection object  → on success
#   None                               → on failure (logs the error)
# ─────────────────────────────────────────────────────────────
def get_connection():
    """
    Create and return a MySQL database connection.

    Reads credentials from environment variables so that no
    passwords ever appear in source code.

    Returns:
        connection (mysql.connector.MySQLConnection) or None
    """
    try:
        # mysql.connector.connect() opens a TCP socket to the MySQL
        # server and authenticates with the provided credentials.
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),   # Server address
            port=int(os.getenv("DB_PORT", 3306)),      # Default MySQL port
            user=os.getenv("DB_USER", "root"),         # MySQL username
            password=os.getenv("DB_PASSWORD", ""),     # MySQL password
            database=os.getenv("DB_NAME", "employee_db")  # Which DB to use
        )

        # connection.is_connected() returns True if the TCP handshake
        # with MySQL succeeded.  It is a quick sanity-check.
        if connection.is_connected():
            return connection  # ← hand the connection back to the caller

    except Error as e:
        # Error is the base exception for ALL mysql-connector errors.
        # Catching it here means we handle "wrong password", "server
        # down", "unknown database", etc., in one place.
        print(f"[database.py] MySQL connection failed: {e}")
        return None  # The caller must check for None before using it


# ── create_tables() ──────────────────────────────────────────
# Runs the CREATE TABLE statement once when the app starts.
# Using "CREATE TABLE IF NOT EXISTS" makes it safe to call
# multiple times — it does nothing if the table already exists.
# ─────────────────────────────────────────────────────────────
def create_tables():
    """
    Create the 'employees' table if it does not already exist.

    Called once from main.py during application startup so the
    database is always ready before the first API request arrives.
    """
    # SQL for the employees table.
    # ── Column explanations ───────────────────────────────────
    # id         INT AUTO_INCREMENT PRIMARY KEY
    #            → MySQL assigns a unique integer automatically.
    #              PRIMARY KEY means no two rows share the same id.
    #              You never insert an id manually.
    #
    # name       VARCHAR(100) NOT NULL
    #            → A string up to 100 characters long.
    #              NOT NULL means the column cannot be empty.
    #
    # email      VARCHAR(150) NOT NULL UNIQUE
    #            → UNIQUE means no two employees can share an email.
    #              MySQL enforces this at the database level, not just
    #              in our Python code.  If you try to insert a duplicate
    #              email, MySQL raises an IntegrityError.
    #
    # department VARCHAR(100) NOT NULL
    #            → Which team the employee belongs to.
    #
    # salary     DECIMAL(10, 2) NOT NULL
    #            → Stores money accurately.  DECIMAL avoids the
    #              floating-point rounding errors you get with FLOAT.
    #              10 total digits, 2 after the decimal point.
    #              Example: 99999999.99
    #
    # created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    #            → MySQL fills this in automatically with the current
    #              date and time when a row is inserted.  Handy for
    #              audit trails.
    # ─────────────────────────────────────────────────────────

    create_employees_table = """
    CREATE TABLE IF NOT EXISTS employees (
        id         INT AUTO_INCREMENT PRIMARY KEY,
        name       VARCHAR(100)    NOT NULL,
        email      VARCHAR(150)    NOT NULL UNIQUE,
        department VARCHAR(100)    NOT NULL,
        salary     DECIMAL(10, 2)  NOT NULL,
        created_at TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
    );
    """

    connection = get_connection()   # Ask for a fresh connection

    if connection is None:
        # If we cannot connect, print a clear message and stop.
        # The app will still start but every DB call will fail later.
        print("[database.py] Cannot create tables — no database connection.")
        return

    try:
        # cursor() creates a "cursor" object.
        # Think of it as the pen that writes SQL to the database.
        cursor = connection.cursor()

        cursor.execute(create_employees_table)  # Send the SQL to MySQL

        # commit() tells MySQL: "make these changes permanent".
        # DDL statements (CREATE, ALTER, DROP) usually auto-commit in
        # MySQL, but calling it explicitly is good practice.
        connection.commit()

        print("[database.py] Table 'employees' is ready.")

    except Error as e:
        print(f"[database.py] Error creating tables: {e}")

    finally:
        # finally always runs — even if an exception was raised.
        # We MUST close the cursor and connection to release resources.
        # Unclosed connections will eventually exhaust the MySQL
        # connection pool and crash the server.
        cursor.close()
        connection.close()
