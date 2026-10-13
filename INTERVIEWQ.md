# Top 30 Interview Questions — Employee Management REST API Project

---

## 1. What is a REST API? How did you use it in this project?

**Answer:**
REST (Representational State Transfer) is a design style for web APIs that uses HTTP methods to perform operations on resources.

In this project:
- `GET /employees` → Read all employees
- `POST /employees` → Create a new employee
- `PUT /employees/{id}` → Update an employee
- `DELETE /employees/{id}` → Delete an employee

Each URL is a **resource** and each HTTP method defines the **action** on that resource.

---

## 2. What is FastAPI? Why did you choose it over Flask or Django?

**Answer:**
FastAPI is a modern Python web framework for building REST APIs.

| Feature | FastAPI | Flask | Django |
|---|---|---|---|
| Speed | Very fast | Moderate | Moderate |
| Auto docs | Yes (`/docs`) | No | No |
| Auto validation | Yes (Pydantic) | Manual | Manual |
| Async support | Built-in | Limited | Limited |

I chose FastAPI because it auto-generates Swagger UI docs and validates all input automatically — saving a lot of manual code.

---

## 3. What is Uvicorn? What does `uvicorn main:app --reload` mean?

**Answer:**
Uvicorn is an ASGI server that runs the FastAPI application. It listens for HTTP requests and forwards them to FastAPI.

Breaking down the command:
- `main` → the Python file `main.py`
- `app` → the FastAPI instance created as `app = FastAPI()`
- `--reload` → auto-restarts the server when any `.py` file is saved (development only)

---

## 4. What is Pydantic? How does it validate data in FastAPI?

**Answer:**
Pydantic is a data validation library. In FastAPI, request bodies are defined as Pydantic `BaseModel` classes.

```python
class EmployeeCreate(BaseModel):
    name:       str
    email:      str
    department: str
    salary:     float
```

When a `POST /employees` request arrives:
1. FastAPI reads the JSON body
2. Pydantic checks each field against its declared type
3. If any field is wrong or missing → FastAPI automatically returns **HTTP 422** with a clear error message
4. If all fields are valid → the function runs

---

## 5. What HTTP status codes did you use and why?

**Answer:**

| Code | Meaning | When we return it |
|---|---|---|
| 200 | OK | Successful GET, PUT, DELETE |
| 201 | Created | New employee added via POST |
| 400 | Bad Request | Invalid file extension or format |
| 404 | Not Found | Employee id or file does not exist |
| 409 | Conflict | Duplicate email already registered |
| 413 | Too Large | Uploaded file exceeds 5 MB |
| 422 | Unprocessable Entity | Pydantic validation failed |
| 503 | Service Unavailable | MySQL connection failed |

---

## 6. What is a Primary Key in MySQL? Why is `id` the primary key?

**Answer:**
A Primary Key is a column that uniquely identifies every row in a table. Rules:
- No two rows can have the same primary key value
- It can never be NULL

`id INT AUTO_INCREMENT PRIMARY KEY` means MySQL automatically assigns the next integer (1, 2, 3…) when a row is inserted. We never insert `id` manually — MySQL handles it.

---

## 7. What is a UNIQUE constraint? Where did you use it?

**Answer:**
UNIQUE ensures no two rows can have the same value in that column. MySQL enforces this at the database level.

In this project `email` has a UNIQUE constraint:
```sql
email VARCHAR(150) NOT NULL UNIQUE
```

If you try to insert two employees with `alice@example.com`, MySQL raises an `IntegrityError`. In Python, we catch it and return HTTP 409 Conflict.

---

## 8. What is SQL Injection? How did you prevent it?

**Answer:**
SQL Injection is an attack where a user enters SQL code as input data to manipulate the database.

**Dangerous (never do this):**
```python
sql = f"SELECT * FROM employees WHERE name = '{name}'"
# If name = "'; DROP TABLE employees; --"  → table destroyed
```

**Safe (parameterized query):**
```python
cursor.execute("SELECT * FROM employees WHERE name = %s", (name,))
```
The `%s` placeholder tells mysql-connector to treat the value as **data**, not SQL code. The value is automatically escaped.

---

## 9. What is `connection.commit()` and why is it needed?

**Answer:**
`commit()` makes database changes permanent. MySQL uses transactions — changes made by INSERT, UPDATE, DELETE exist only in memory until `commit()` is called.

Without `commit()`:
- The change appears to work
- But when the connection closes, the change is **rolled back** (lost)

Think of it as pressing **Save** in a document.

---

## 10. What does `cursor.rowcount` tell you? Give a real example.

**Answer:**
After an UPDATE or DELETE, `cursor.rowcount` returns the number of rows that were actually changed.

```python
cursor.execute("DELETE FROM employees WHERE id = %s", (employee_id,))
if cursor.rowcount == 0:
    # No row was deleted — that id does not exist
    raise HTTPException(status_code=404, detail="Employee not found")
```

This is how we distinguish between "successfully deleted" and "id not found".

---

## 11. What is the difference between `fetchone()` and `fetchall()`?

**Answer:**

| Method | Returns | Used for |
|---|---|---|
| `fetchone()` | One row dict or `None` | `GET /employees/{id}` — single employee |
| `fetchall()` | List of all matching rows | `GET /employees` — all employees |

`fetchone()` returns `None` when no row matches the query — that's how we know an employee id doesn't exist.

---

## 12. What is `cursor(dictionary=True)` and why did you use it?

**Answer:**
By default, mysql-connector returns rows as **tuples**:
```python
(1, "Alice", "alice@example.com", "Engineering", 75000.00)
```

With `dictionary=True`, rows come back as **dicts**:
```python
{"id": 1, "name": "Alice", "email": "alice@example.com", ...}
```

Dicts are much easier to work with because you access values by name (`row["name"]`) instead of index (`row[1]`). FastAPI also converts dicts directly to JSON responses.

---

## 13. What is the purpose of `database.py`? Why keep it separate?

**Answer:**
`database.py` has one single job — provide a working MySQL connection to the rest of the application.

Keeping it separate means:
- If we switch from MySQL to PostgreSQL, we only change `database.py`
- No SQL queries live here — just connection logic
- Every other file just calls `get_connection()` without knowing the details

This is called **Separation of Concerns**.

---

## 14. What is `@app.on_event("startup")` used for?

**Answer:**
It registers a function that runs **once** when the server starts, before the first request arrives.

In this project it calls `create_tables()` which runs:
```sql
CREATE TABLE IF NOT EXISTS employees (...)
```

This ensures the table always exists before any API request tries to use it. `IF NOT EXISTS` makes it safe to call every startup — it does nothing if the table is already there.

---

## 15. What is the difference between `open()` modes `"r"`, `"w"`, and `"a"`?

**Answer:**

| Mode | Full name | Behaviour |
|---|---|---|
| `"r"` | Read | Opens existing file. Fails if file doesn't exist. |
| `"w"` | Write | Creates file OR erases existing content, then writes fresh. |
| `"a"` | Append | Creates file OR adds new content to the END without erasing. |
| `"x"` | Exclusive create | Creates new file. Fails if file already exists. |
| `"rb"/"wb"` | Binary | Read/write raw bytes — used for uploaded file content. |

---

## 16. What is a path traversal attack? How did you prevent it?

**Answer:**
A path traversal attack is when a user sends a filename like `../../etc/passwd` trying to access files outside the allowed folder.

Prevention with `_safe_path()` in `file_operations.py`:
```python
full_path = (folder / filename).resolve()
if not str(full_path).startswith(str(folder.resolve())):
    raise ValueError("Access denied")
```

`resolve()` expands all `..` and symlinks to an absolute path. If the resolved path is outside the `uploads/` folder, the request is rejected immediately.

---

## 17. What is `csv.DictReader`? How did you use it for CSV import?

**Answer:**
`csv.DictReader` reads a CSV file and returns each row as a Python dictionary using the header row as keys.

```python
with open("employees.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        print(row["name"], row["salary"])
        # row → {"name": "Alice", "email": "...", "department": "...", "salary": "75000"}
```

In the CSV import endpoint, we loop through all rows, validate each one (check salary is a number, email has `@`, etc.), separate valid from invalid rows, then bulk-insert the valid ones into MySQL.

---

## 18. What is `json.load()` vs `json.loads()`?

**Answer:**

| Function | Input | Used for |
|---|---|---|
| `json.load(f)` | File object | Reading JSON directly from a file |
| `json.loads(s)` | String | Parsing a JSON string already in memory |

```python
# From file
with open("employees.json") as f:
    data = json.load(f)

# From string
data = json.loads('{"name": "Alice"}')
```

`json.JSONDecodeError` is raised if the content is not valid JSON syntax.

---

## 19. What is `json.dump()` and what does `indent=4` do?

**Answer:**
`json.dump(data, file)` serializes a Python object (dict or list) and writes it to a file as JSON.

`indent=4` makes the output **pretty-printed** with 4 spaces of indentation per level — human-readable instead of one long line.

`default=str` handles types like `Decimal` and `datetime` that are not natively JSON-serializable by converting them to strings.

```python
with open("export.json", "w") as f:
    json.dump(employees, f, indent=4, default=str)
```

---

## 20. What is `UploadFile` in FastAPI? How does file upload work?

**Answer:**
`UploadFile` represents a file sent by the client as `multipart/form-data`. It gives access to:
- `file.filename` → original name of the uploaded file
- `await file.read()` → raw bytes of the file content
- `file.content_type` → MIME type of the file

The `await` is needed because reading bytes from the network is an async I/O operation.

In Postman, file uploads are sent via **Body → form-data → key: file (type: File)**.

---

## 21. How did you validate uploaded files?

**Answer:**
Two checks before saving to disk:

1. **Extension check** — only `.txt`, `.csv`, `.json` allowed:
```python
ext = Path(filename).suffix.lower()
if ext not in {".txt", ".csv", ".json"}:
    raise HTTPException(status_code=400, detail="Extension not allowed")
```

2. **Size check** — maximum 5 MB:
```python
if len(content) > max_size:
    raise HTTPException(status_code=413, detail="File too large")
```

Both checks happen **before** saving to disk so invalid files are never stored.

---

## 22. What is `FileResponse` in FastAPI? When did you use it?

**Answer:**
`FileResponse` streams a file from disk directly to the HTTP client. The browser receives the file as a download.

```python
return FileResponse(
    path="reports/employees_export.csv",
    filename="employees_export.csv",
    media_type="application/octet-stream"
)
```

Used in the download endpoints (`/files/download/upload/{filename}` and `/files/download/report/{filename}`).

`media_type="application/octet-stream"` is a generic binary type that triggers a "Save As" dialog in the browser.

---

## 23. What is a `.env` file? Why should it never be committed to GitHub?

**Answer:**
`.env` stores sensitive configuration values:
```
DB_PASSWORD=mypassword123
DB_HOST=localhost
```

`python-dotenv` reads it at startup and loads values into `os.environ`. The code reads them with `os.getenv("DB_PASSWORD")`.

**Why not commit to GitHub:**
- If pushed, anyone with repo access sees the password
- Even in a private repo, third-party GitHub apps may have access
- Git history retains the password permanently even after deletion

Always add `.env` to `.gitignore` before the first `git add`.

---

## 24. What is `os.getenv()` and what does the default value do?

**Answer:**
`os.getenv("KEY", "default")` reads an environment variable.

- If the variable exists → returns its value
- If not set → returns the default value instead of crashing

```python
host = os.getenv("DB_HOST", "localhost")
# Returns "localhost" if DB_HOST is not in .env
```

This makes the application resilient when `.env` is missing a key.

---

## 25. What is the difference between `IntegrityError` and `Error` in mysql-connector?

**Answer:**

| Exception | When raised | Used for |
|---|---|---|
| `IntegrityError` | UNIQUE or FK constraint violated | Duplicate email → return 409 |
| `Error` | Any other MySQL problem | Connection failure, syntax error → return 500 |

We catch `IntegrityError` **first** to give a specific user-friendly message, then catch the general `Error` for everything else:

```python
except IntegrityError:
    return {"success": False, "error": "Duplicate email"}
except Error as e:
    return {"success": False, "error": str(e)}
```

---

## 26. What is the purpose of `try`, `except`, `else`, `finally`?

**Answer:**

```python
try:
    # Code that might raise an exception
    result = risky_operation()

except SpecificError as e:
    # Handles a known error type specifically
    print(f"Known error: {e}")

except Exception as e:
    # Catch-all for unexpected errors
    print(f"Unexpected: {e}")

else:
    # Runs ONLY if the try block succeeded (no exception)
    print("Success!")

finally:
    # ALWAYS runs — with or without exception
    # Used for cleanup: close files, close DB connections
    cursor.close()
    connection.close()
```

---

## 27. What is `LIKE` in SQL? How did you implement search?

**Answer:**
`LIKE` is used for partial text matching in SQL. The `%` wildcard matches any number of characters.

```sql
SELECT * FROM employees
WHERE name LIKE '%alice%' OR department LIKE '%alice%'
```

In Python:
```python
like_pattern = f"%{keyword}%"
cursor.execute(
    "SELECT * FROM employees WHERE name LIKE %s OR department LIKE %s",
    (like_pattern, like_pattern)
)
```

Searching `engineering` would match `Engineering`, `Software Engineering`, etc.

---

## 28. What is `bulk_insert_employees()` and why is it better than calling `add_employee()` in a loop?

**Answer:**
`add_employee()` opens a new DB connection for every single row. With 1000 rows that means 1000 connection overheads — very slow.

`bulk_insert_employees()` opens **one connection** and inserts all rows through it, committing each row individually so a duplicate email skips that row without stopping the rest.

This is significantly faster for CSV/JSON imports with many rows.

---

## 29. What is `Path(__file__).parent` in `file_operations.py`?

**Answer:**
`__file__` is a special Python variable that holds the absolute path of the current script file.

`Path(__file__).parent` gives the **directory** that contains the script.

```python
BASE_DIR   = Path(__file__).parent          # .../employee_api/
UPLOAD_DIR = BASE_DIR / "uploads"           # .../employee_api/uploads/
```

Using `Path(__file__).parent` means the path always works correctly regardless of which directory the user runs the server from. It is relative to the file itself, not the working directory.

---

## 30. How would you improve this project if it went to production?

**Answer:**

| Area | Improvement |
|---|---|
| **Security** | Add JWT authentication so only logged-in users can access the API |
| **Database** | Use a connection pool (e.g., `mysql-connector` pooling) instead of opening a new connection per request |
| **Performance** | Add pagination to `GET /employees` — returning 10,000 rows at once is slow |
| **File storage** | Store uploaded files on AWS S3 or Azure Blob Storage instead of local disk |
| **Logging** | Replace `print()` with Python's `logging` module, writing logs to a file |
| **Testing** | Write unit tests with `pytest` for every function |
| **HTTPS** | Use HTTPS in production (via a reverse proxy like Nginx) |
| **PATCH support** | Add `PATCH /employees/{id}` for partial updates instead of only full PUT |
| **Rate limiting** | Limit requests per IP to prevent abuse |
| **Validation** | Add more specific email format validation and salary upper-limit checks |
