# Employee Management REST API

A beginner-friendly REST API built with **Python**, **FastAPI**, **MySQL**, and file handling.

---

## Project Structure

```
employee_api/
├── main.py               ← FastAPI app: all HTTP routes
├── database.py           ← MySQL connection factory + table creation
├── employee_queries.py   ← All SQL queries (add, get, update, delete, search)
├── file_operations.py    ← Text, CSV, JSON, upload/download helpers
├── uploads/              ← Uploaded files are saved here
├── reports/              ← Exported CSV/JSON reports are saved here
├── requirements.txt      ← Python package list
├── .env                  ← Database credentials (NEVER commit this)
└── README.md             ← This file
```

### File responsibilities

| File | What it does |
|---|---|
| `main.py` | Defines every URL route. Validates HTTP input using Pydantic. Calls query and file functions. |
| `database.py` | Opens MySQL connections. Creates tables on startup. |
| `employee_queries.py` | All SQL: INSERT, SELECT, UPDATE, DELETE, LIKE search, bulk insert. |
| `file_operations.py` | Text file CRUD, CSV read/write/validate, JSON read/write, upload/download path helpers. |

---

## Stage 1 — Set Up Python and Virtual Environment

### Why a virtual environment?
A virtual environment is an isolated Python installation for one project.
Packages installed inside it do not affect other projects on your machine.

### Steps

```powershell
# 1. Open a terminal inside the employee_api folder
cd d:\nighan2\Rest-API-Using-Python-and-MySQL\employee_api

# 2. Create a virtual environment named .venv
python -m venv .venv

# 3. Activate it (Windows PowerShell)
.venv\Scripts\Activate.ps1

# 4. Install all packages
pip install -r requirements.txt
```

You should see `(.venv)` at the start of your terminal prompt.

---

## Stage 2 — Create the MySQL Database

Open MySQL Workbench or the MySQL CLI and run:

```sql
-- Create the database
CREATE DATABASE IF NOT EXISTS employee_db;

-- Select it
USE employee_db;

-- The table is created automatically when the app starts,
-- but you can also create it manually:
CREATE TABLE IF NOT EXISTS employees (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100)   NOT NULL,
    email      VARCHAR(150)   NOT NULL UNIQUE,
    department VARCHAR(100)   NOT NULL,
    salary     DECIMAL(10,2)  NOT NULL,
    created_at TIMESTAMP      DEFAULT CURRENT_TIMESTAMP
);
```

### Key concepts

| Concept | Explanation |
|---|---|
| `PRIMARY KEY` | A column that uniquely identifies every row. No two rows can share the same id. |
| `AUTO_INCREMENT` | MySQL automatically assigns the next integer when a row is inserted. |
| `NOT NULL` | The column must have a value — you cannot leave it blank. |
| `UNIQUE` | No two rows can have the same value in this column. MySQL enforces this. |
| `DECIMAL(10,2)` | Stores numbers exactly (no floating-point errors). 10 total digits, 2 after the decimal. |
| `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` | MySQL fills this in automatically with the current date and time. |

---

## Stage 3 — Configure the .env File

Edit `employee_api/.env` and fill in YOUR MySQL credentials:

```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_real_password_here
DB_NAME=employee_db
```

**Never commit `.env` to GitHub.** The `.gitignore` already excludes it.

---

## Stage 4 — Run the API

```powershell
# Make sure .venv is activated, then:
uvicorn main:app --reload
```

- `main` → the filename `main.py`
- `app`  → the FastAPI instance created with `app = FastAPI(…)`
- `--reload` → restarts the server automatically when you save a file

Open your browser: **http://127.0.0.1:8000/docs**

This is the interactive API documentation (Swagger UI). You can test every endpoint from the browser.

---

## Stage 5 — Employee CRUD APIs

### Add an employee

```
POST http://127.0.0.1:8000/employees
Content-Type: application/json

{
  "name": "Alice Johnson",
  "email": "alice@example.com",
  "department": "Engineering",
  "salary": 75000.00
}
```

Expected response (201 Created):
```json
{
  "message": "Employee created successfully",
  "id": 1
}
```

### Get all employees

```
GET http://127.0.0.1:8000/employees
```

### Get one employee

```
GET http://127.0.0.1:8000/employees/1
```

### Update an employee

```
PUT http://127.0.0.1:8000/employees/1
Content-Type: application/json

{
  "name": "Alice Johnson",
  "email": "alice.new@example.com",
  "department": "Product",
  "salary": 85000.00
}
```

### Delete an employee

```
DELETE http://127.0.0.1:8000/employees/1
```

### Search employees

```
GET http://127.0.0.1:8000/employees/search/query?keyword=eng
```

---

## Stage 6 — Text File APIs

All files are stored inside `uploads/`.

| Method | URL | What it does |
|---|---|---|
| POST | `/files/text/create?filename=notes.txt` | Create empty file |
| PUT | `/files/text/write?filename=notes.txt&content=Hello` | Write (overwrite) content |
| PUT | `/files/text/append?filename=notes.txt&content=World` | Append content |
| GET | `/files/text/read?filename=notes.txt` | Read full content |
| GET | `/files/text/read-lines?filename=notes.txt` | Read line by line |
| GET | `/files/text/exists?filename=notes.txt` | Check if file exists |
| PUT | `/files/text/rename?old_filename=notes.txt&new_filename=renamed.txt` | Rename file |
| PUT | `/files/text/copy?source_filename=notes.txt&dest_filename=backup.txt` | Copy file |
| DELETE | `/files/text/delete?filename=notes.txt` | Delete file |
| GET | `/files/text/size?filename=notes.txt` | Get file size |

---

## Stage 7 — CSV Import and Export

### Import CSV

Postman:
- Method: `POST`
- URL: `http://127.0.0.1:8000/files/csv/import`
- Body → `form-data` → key: `file` (type: File) → select your CSV

CSV format:
```
name,email,department,salary
Alice,alice@example.com,Engineering,75000
Bob,bob@example.com,HR,55000
```

### Export CSV

```
GET http://127.0.0.1:8000/files/csv/export
```

Then download the report:
```
GET http://127.0.0.1:8000/files/download/report/employees_export.csv
```

---

## Stage 8 — JSON Import and Export

### Import JSON

Postman:
- Method: `POST`
- URL: `http://127.0.0.1:8000/files/json/import`
- Body → `form-data` → key: `file` (type: File) → select your JSON

JSON format:
```json
[
  {"name": "Alice", "email": "alice@example.com", "department": "Engineering", "salary": 75000},
  {"name": "Bob",   "email": "bob@example.com",   "department": "HR",          "salary": 55000}
]
```

### Export JSON

```
GET http://127.0.0.1:8000/files/json/export
```

Then download:
```
GET http://127.0.0.1:8000/files/download/report/employees_export.json
```

---

## Stage 9 — File Upload and Download

### Upload any file (.txt, .csv, .json)

Postman:
- Method: `POST`
- URL: `http://127.0.0.1:8000/files/upload`
- Body → `form-data` → key: `file` (type: File)

### Download an uploaded file

```
GET http://127.0.0.1:8000/files/download/upload/yourfile.csv
```

---

## Error Handling Reference

| Situation | HTTP Status | Detail |
|---|---|---|
| Invalid input (missing field, wrong type) | 422 | FastAPI auto-validates via Pydantic |
| Employee not found | 404 | "Employee with id X not found." |
| Duplicate email | 409 | "Email '…' is already registered." |
| Invalid file extension | 400 | "Extension '.exe' not allowed." |
| File too large | 413 | "File exceeds maximum size of 5 MB." |
| File not found (download) | 404 | "File '…' not found." |
| Invalid CSV format | 400 | "Missing columns: {'salary'}" |
| Invalid JSON | 400 | "Invalid JSON: …" |
| Database unavailable | 503 | "Database is unavailable." |

---

## Postman Testing Steps

1. Download and install [Postman](https://www.postman.com/downloads/)
2. Create a new Collection called "Employee API"
3. For each request:
   - Set the correct HTTP method (GET / POST / PUT / DELETE)
   - Enter the URL
   - For POST and PUT requests: go to **Body** → select **raw** → choose **JSON** → paste the JSON
   - For file uploads: go to **Body** → select **form-data** → add key `file` with type **File**
4. Click **Send** and read the response in the bottom panel

---

## Common Errors and Fixes

| Error | Likely Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'fastapi'` | Virtual env not activated | Run `.venv\Scripts\Activate.ps1` |
| `Access denied for user 'root'@'localhost'` | Wrong DB_PASSWORD in .env | Fix the password in `.env` |
| `Unknown database 'employee_db'` | Database not created | Run `CREATE DATABASE employee_db;` in MySQL |
| `Address already in use` | Another process on port 8000 | Add `--port 8001` to the uvicorn command |
| `422 Unprocessable Entity` | Bad JSON input | Check the request body matches the expected schema |

---

## Interview Questions

### Q1. What is a REST API?
A REST API (Representational State Transfer) is a way for two applications to communicate over HTTP using standard methods: GET (read), POST (create), PUT (update), DELETE (delete).

### Q2. What is the difference between PUT and PATCH?
- **PUT** replaces the entire resource. You must send all fields.
- **PATCH** updates only the fields you send. Partial update.

### Q3. Why do we use parameterized queries (%s) instead of string formatting?
String formatting allows SQL Injection attacks. Parameterized queries escape the values safely, so user input cannot alter the SQL structure.

### Q4. What is the purpose of `.env` and `python-dotenv`?
`.env` stores sensitive credentials outside of source code. `python-dotenv` loads those values into `os.environ` so the Python code reads them with `os.getenv()`. This prevents secrets from being committed to Git.

### Q5. What does `cursor.rowcount` tell you?
After an UPDATE or DELETE, `cursor.rowcount` contains the number of rows that were actually changed. If it is 0, the WHERE clause matched no rows (the id did not exist).

---

## Practice Tasks

1. Add a new endpoint `GET /employees/department/{dept_name}` that returns all employees in a specific department.
2. Add a `PATCH /employees/{id}/salary` endpoint that updates ONLY the salary of an employee without changing the other fields.
