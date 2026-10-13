# ─────────────────────────────────────────────────────────────
# employee_queries.py
# ─────────────────────────────────────────────────────────────
# Responsibility:
#   All SQL queries related to employees live here.
#   This file talks directly to the database and returns plain
#   Python dictionaries or lists.
#
#   It does NOT know about HTTP, FastAPI, or JSON.
#   That separation makes each piece easy to test and change.
#
# Pattern used (simple functions, no classes):
#   Each function:
#     1. Gets a connection from database.py
#     2. Runs one SQL statement
#     3. Returns the result
#     4. Closes cursor + connection in a finally block
# ─────────────────────────────────────────────────────────────

from mysql.connector import Error, IntegrityError  # MySQL exception types
from database import get_connection                 # Our connection factory


# ── Helper ───────────────────────────────────────────────────
# cursor(dictionary=True) tells mysql-connector to return each
# row as a Python dict  {"id": 1, "name": "Alice", …}  instead
# of a plain tuple (1, "Alice", …).
# Dicts are much easier to work with because keys are self-documenting.
# ─────────────────────────────────────────────────────────────


# ╔══════════════════════════════════════════════════════════════╗
# ║  1. ADD EMPLOYEE                                             ║
# ╚══════════════════════════════════════════════════════════════╝
def add_employee(name: str, email: str, department: str, salary: float):
    """
    Insert a new employee row into the employees table.

    Args:
        name       : Employee's full name
        email      : Unique email address
        department : Department name
        salary     : Monthly salary (decimal)

    Returns:
        dict with "success" True and the new employee's id, OR
        dict with "success" False and an "error" message.

    SQL used:
        INSERT INTO employees (name, email, department, salary)
        VALUES (%s, %s, %s, %s)

    Why %s placeholders?
        Using %s (parameterized query) instead of string formatting
        ("INSERT … VALUES ('" + name + "')") prevents SQL Injection.
        SQL Injection is when a malicious user types SQL code as
        their name, e.g., name = "'; DROP TABLE employees; --"
        With %s, mysql-connector escapes the value safely.
    """
    connection = get_connection()
    if connection is None:
        return {"success": False, "error": "Database connection failed"}

    cursor = None
    try:
        cursor = connection.cursor()

        sql = """
            INSERT INTO employees (name, email, department, salary)
            VALUES (%s, %s, %s, %s)
        """
        # The second argument to cursor.execute() is a TUPLE of values.
        # mysql-connector maps the first %s → name, second → email, etc.
        values = (name, email, department, salary)
        cursor.execute(sql, values)

        connection.commit()  # Make the INSERT permanent

        # cursor.lastrowid holds the auto-generated id of the row we
        # just inserted.  MySQL fills this in because of AUTO_INCREMENT.
        new_id = cursor.lastrowid
        return {"success": True, "id": new_id}

    except IntegrityError as e:
        # IntegrityError is raised when a UNIQUE constraint is violated.
        # That happens when we try to insert an email that already exists.
        return {"success": False, "error": f"Duplicate email — {e}"}

    except Error as e:
        return {"success": False, "error": str(e)}

    finally:
        if cursor:
            cursor.close()
        connection.close()


# ╔══════════════════════════════════════════════════════════════╗
# ║  2. GET ALL EMPLOYEES                                        ║
# ╚══════════════════════════════════════════════════════════════╝
def get_all_employees():
    """
    Fetch every row from the employees table.

    Returns:
        list of dicts, e.g.:
        [{"id": 1, "name": "Alice", "email": "…", …}, …]

        Empty list [] if no employees exist.
        None if the database call failed.

    SQL used:
        SELECT * FROM employees ORDER BY id
    """
    connection = get_connection()
    if connection is None:
        return None

    cursor = None
    try:
        # dictionary=True → rows come back as dicts, not tuples
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT * FROM employees ORDER BY id")

        # fetchall() retrieves every result row into a Python list.
        # If there are no rows, it returns an empty list — never None.
        employees = cursor.fetchall()
        return employees

    except Error as e:
        print(f"[employee_queries] get_all_employees error: {e}")
        return None

    finally:
        if cursor:
            cursor.close()
        connection.close()


# ╔══════════════════════════════════════════════════════════════╗
# ║  3. GET EMPLOYEE BY ID                                       ║
# ╚══════════════════════════════════════════════════════════════╝
def get_employee_by_id(employee_id: int):
    """
    Fetch a single employee row by primary key.

    Args:
        employee_id : The integer id to look up

    Returns:
        dict  → employee found
        None  → no employee with that id (or DB error)

    SQL used:
        SELECT * FROM employees WHERE id = %s
    """
    connection = get_connection()
    if connection is None:
        return None

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM employees WHERE id = %s", (employee_id,))

        # fetchone() returns ONE row dict, or None if no row matched.
        # Note the trailing comma in (employee_id,) — that makes it a
        # tuple.  Without the comma, Python treats it as just parentheses
        # around the integer, which is NOT a tuple and would crash.
        employee = cursor.fetchone()
        return employee

    except Error as e:
        print(f"[employee_queries] get_employee_by_id error: {e}")
        return None

    finally:
        if cursor:
            cursor.close()
        connection.close()


# ╔══════════════════════════════════════════════════════════════╗
# ║  4. UPDATE EMPLOYEE                                          ║
# ╚══════════════════════════════════════════════════════════════╝
def update_employee(employee_id: int, name: str, email: str,
                    department: str, salary: float):
    """
    Update all fields of an existing employee row.

    Args:
        employee_id : Which row to update (WHERE id = …)
        name, email, department, salary : New values

    Returns:
        dict with "success" True and "rows_affected" count, OR
        dict with "success" False and "error" message.

    SQL used:
        UPDATE employees
        SET name=%s, email=%s, department=%s, salary=%s
        WHERE id=%s

    Important:
        cursor.rowcount after UPDATE tells us how many rows were
        changed.  If rowcount == 0, the id did not exist.
    """
    connection = get_connection()
    if connection is None:
        return {"success": False, "error": "Database connection failed"}

    cursor = None
    try:
        cursor = connection.cursor()

        sql = """
            UPDATE employees
            SET name = %s, email = %s, department = %s, salary = %s
            WHERE id = %s
        """
        # Values tuple — order must match the %s placeholders above
        values = (name, email, department, salary, employee_id)
        cursor.execute(sql, values)
        connection.commit()

        return {"success": True, "rows_affected": cursor.rowcount}

    except IntegrityError as e:
        return {"success": False, "error": f"Duplicate email — {e}"}

    except Error as e:
        return {"success": False, "error": str(e)}

    finally:
        if cursor:
            cursor.close()
        connection.close()


# ╔══════════════════════════════════════════════════════════════╗
# ║  5. DELETE EMPLOYEE                                          ║
# ╚══════════════════════════════════════════════════════════════╝
def delete_employee(employee_id: int):
    """
    Delete the employee row with the given id.

    Returns:
        dict with "success" True and "rows_affected", OR
        dict with "success" False and "error" message.

    SQL used:
        DELETE FROM employees WHERE id = %s
    """
    connection = get_connection()
    if connection is None:
        return {"success": False, "error": "Database connection failed"}

    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM employees WHERE id = %s", (employee_id,))
        connection.commit()
        return {"success": True, "rows_affected": cursor.rowcount}

    except Error as e:
        return {"success": False, "error": str(e)}

    finally:
        if cursor:
            cursor.close()
        connection.close()


# ╔══════════════════════════════════════════════════════════════╗
# ║  6. SEARCH EMPLOYEES                                         ║
# ╚══════════════════════════════════════════════════════════════╝
def search_employees(keyword: str):
    """
    Search employees whose name OR department contains the keyword.

    Args:
        keyword : Free-text search term (case-insensitive in MySQL)

    Returns:
        list of matching employee dicts, or None on error.

    SQL used:
        SELECT * FROM employees
        WHERE name LIKE %s OR department LIKE %s
        ORDER BY name

    LIKE '%keyword%' means:
        % matches any number of any characters.
        So '%eng%' would match "Engineering", "Penguin Dept", etc.
        The % wildcards are added in Python, not in the SQL string,
        so we can still use a parameterized query safely.
    """
    connection = get_connection()
    if connection is None:
        return None

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)

        # Wrap the keyword in % wildcards for a "contains" search
        like_pattern = f"%{keyword}%"

        sql = """
            SELECT * FROM employees
            WHERE name LIKE %s OR department LIKE %s
            ORDER BY name
        """
        cursor.execute(sql, (like_pattern, like_pattern))
        results = cursor.fetchall()
        return results

    except Error as e:
        print(f"[employee_queries] search_employees error: {e}")
        return None

    finally:
        if cursor:
            cursor.close()
        connection.close()


# ╔══════════════════════════════════════════════════════════════╗
# ║  7. BULK INSERT (used by CSV import)                         ║
# ╚══════════════════════════════════════════════════════════════╝
def bulk_insert_employees(employee_list: list):
    """
    Insert multiple employee rows in a single database round-trip.

    Args:
        employee_list : list of dicts, each with keys:
                        name, email, department, salary

    Returns:
        dict with "success" True, "inserted" count, "skipped" count.

    Why bulk insert?
        Calling add_employee() in a loop opens and closes a new DB
        connection for every row.  With 1000 rows that means 1000
        connection overheads.  executemany() sends them all at once.
    """
    connection = get_connection()
    if connection is None:
        return {"success": False, "error": "Database connection failed"}

    cursor = None
    inserted = 0
    skipped = 0

    try:
        cursor = connection.cursor()

        sql = """
            INSERT INTO employees (name, email, department, salary)
            VALUES (%s, %s, %s, %s)
        """

        for emp in employee_list:
            try:
                values = (
                    emp["name"],
                    emp["email"],
                    emp["department"],
                    emp["salary"]
                )
                cursor.execute(sql, values)
                connection.commit()
                inserted += 1

            except IntegrityError:
                # Duplicate email — skip this row, continue with the rest
                connection.rollback()  # Roll back only this one row
                skipped += 1

        return {"success": True, "inserted": inserted, "skipped": skipped}

    except Error as e:
        return {"success": False, "error": str(e)}

    finally:
        if cursor:
            cursor.close()
        connection.close()


# ╔══════════════════════════════════════════════════════════════╗
# ║  8. GET ALL EMPLOYEES AS PLAIN DICTS (for export)           ║
# ╚══════════════════════════════════════════════════════════════╝
def get_employees_for_export():
    """
    Fetch all employees with only the columns we want to export.
    Excludes 'created_at' to keep exports clean.

    Returns:
        list of dicts with keys: id, name, email, department, salary
    """
    connection = get_connection()
    if connection is None:
        return None

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, name, email, department, salary "
            "FROM employees ORDER BY id"
        )
        return cursor.fetchall()

    except Error as e:
        print(f"[employee_queries] get_employees_for_export error: {e}")
        return None

    finally:
        if cursor:
            cursor.close()
        connection.close()
