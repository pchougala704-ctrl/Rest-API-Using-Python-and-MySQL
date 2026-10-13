# Employee Management REST API

A beginner-friendly REST API built with **Python**, **FastAPI**, **MySQL**, and file handling.

---

## How to Run

> Complete these 4 commands in order. That's all it takes.

```powershell
# 1. Go into the project folder
cd d:\nighan2\Rest-API-Using-Python-and-MySQL\employee_api

# 2. Create and activate the virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# 3. Install packages
pip install -r requirements.txt

# 4. Start the server
uvicorn main:app --reload
```

The server is running when you see:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
[database.py] Table 'employees' is ready.
[main.py] Ready to accept requests.
```

**Before step 4**, make sure you have:
- Created the MySQL database → `CREATE DATABASE employee_db;`
- Filled in your MySQL password in `employee_api/.env`

To stop the server: press `Ctrl + C`

---

## How to Use

### Option A — Interactive browser docs (easiest)

Open **http://127.0.0.1:8000/docs** in your browser.

Every endpoint is listed. Click any one → click **Try it out** → fill in the fields → click **Execute**. You see the real response right there.

### Option B — Postman

1. Open Postman → **New** → **HTTP Request**
2. Set the method (GET / POST / PUT / DELETE)
3. Enter the URL, e.g. `http://127.0.0.1:8000/employees`
4. For POST / PUT: go to **Body** → **raw** → **JSON** → paste the JSON body
5. For file uploads: go to **Body** → **form-data** → key `file`, type **File** → pick your file
6. Click **Send**

### Quick usage examples

**Add an employee**
```
POST http://127.0.0.1:8000/employees
Body (JSON):
{
  "name": "Alice Johnson",
  "email": "alice@example.com",
  "department": "Engineering",
  "salary": 75000.00
}
```

**Get all employees**
```
GET http://127.0.0.1:8000/employees
```

**Get one employee**
```
GET http://127.0.0.1:8000/employees/1
```

**Update an employee**
```
PUT http://127.0.0.1:8000/employees/1
Body (JSON):
{
  "name": "Alice Johnson",
  "email": "alice@example.com",
  "department": "Product",
  "salary": 85000.00
}
```

**Delete an employee**
```
DELETE http://127.0.0.1:8000/employees/1
```

**Search by name or department**
```
GET http://127.0.0.1:8000/employees/search/query?keyword=engineering
```

**Upload a CSV file**
```
POST http://127.0.0.1:8000/files/upload
Body → form-data → key: file (type: File) → select employees.csv
```

**Export all employees to CSV**
```
GET http://127.0.0.1:8000/files/csv/export
GET http://127.0.0.1:8000/files/download/report/employees_export.csv
```

---

## Tech Stack

| Technology | Role |
|---|---|
| Python | Core programming language |
| FastAPI | Web framework — defines HTTP routes |
| MySQL | Relational database — stores employee records |
| Uvicorn | ASGI server — runs the FastAPI app |
| mysql-connector-python | MySQL driver for Python |
| python-dotenv | Reads `.env` credentials into `os.environ` |
| python-multipart | Enables file upload support |
| Postman | API testing tool |

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

---

## Step-by-Step Setup

---

### Step 1 — Prerequisites

Make sure you have these installed before starting:

- [Python 3.10+](https://www.python.org/downloads/) — verify with `python --version`
- [MySQL 8.0+](https://dev.mysql.com/downloads/mysql/) — verify with `mysql --version`
- [VS Code](https://code.visualstudio.com/) — recommended editor
- [Postman](https://www.postman.com/downloads/) — for testing the API

---

### Step 2 — Clone or Download the Project

If you cloned from GitHub:

```powershell
git clone https://github.com/your-username/Rest-API-Using-Python-and-MySQL.git
cd Rest-API-Using-Python-and-MySQL\employee_api
```

Or simply open the `employee_api` folder in VS Code.

---

### Step 3 — Create a Virtual Environment

A virtual environment keeps packages isolated to this project only.

```powershell
# Run this inside the employee_api folder
python -m venv .venv
```

Activate it:

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1

# Windows CMD
.venv\Scripts\activate.bat

# macOS / Linux
source .venv/bin/activate
```

You will see `(.venv)` at the start of your terminal prompt when it is active.

> **Tip:** If PowerShell blocks the activation script, run this once:
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

---

### Step 4 — Install Dependencies

```powershell
pip install -r requirements.txt
```

What gets installed:

```
fastapi==0.111.0          ← Web framework
uvicorn==0.29.0           ← Server to run FastAPI
mysql-connector-python==8.4.0  ← MySQL driver
python-dotenv==1.0.1      ← Read .env file
python-multipart==0.0.9   ← Enable file uploads
aiofiles==23.2.1          ← Non-blocking file I/O
```

Verify installation:

```powershell
pip list
```

---

### Step 5 — Create the MySQL Database

Open MySQL Workbench or the MySQL CLI and run:

```sql
-- Create the database
CREATE DATABASE IF NOT EXISTS employee_db;

-- Select it
USE employee_db;
```

> The `employees` table is created **automatically** when the app starts for the first time.
> You do not need to create it manually.

If you want to create it manually anyway:

```sql
CREATE TABLE IF NOT EXISTS employees (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100)   NOT NULL,
    email      VARCHAR(150)   NOT NULL UNIQUE,
    department VARCHAR(100)   NOT NULL,
    salary     DECIMAL(10,2)  NOT NULL,
    created_at TIMESTAMP      DEFAULT CURRENT_TIMESTAMP
);
```

**Table column explanations:**

| Column | Type | Rule | Meaning |
|---|---|---|---|
| `id` | INT | PRIMARY KEY, AUTO_INCREMENT | Unique integer, assigned automatically |
| `name` | VARCHAR(100) | NOT NULL | Required, up to 100 characters |
| `email` | VARCHAR(150) | NOT NULL, UNIQUE | Required, no duplicates allowed |
| `department` | VARCHAR(100) | NOT NULL | Required |
| `salary` | DECIMAL(10,2) | NOT NULL | Exact decimal number (e.g. 75000.00) |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Auto-filled by MySQL on insert |

---

### Step 6 — Configure the .env File

Open `employee_api/.env` and fill in your MySQL credentials:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password_here
DB_NAME=employee_db

UPLOAD_FOLDER=uploads
REPORTS_FOLDER=reports
MAX_FILE_SIZE=5242880
```

> **Never commit `.env` to GitHub.** It is already listed in `.gitignore`.

---

### Step 7 — Run the API Server

Make sure your virtual environment is active, then:

```powershell
uvicorn main:app --reload
```

Expected output:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
[main.py] Server starting — creating tables if needed …
[database.py] Table 'employees' is ready.
[main.py] Ready to accept requests.
```

- `main` → the filename `main.py`
- `app`  → the `FastAPI()` instance inside it
- `--reload` → automatically restarts when you save any `.py` file

---

### Step 8 — Open the Interactive Docs

Visit **http://127.0.0.1:8000/docs** in your browser.

This is Swagger UI — an interactive page where you can read about every endpoint and test them directly without Postman.

Also available: **http://127.0.0.1:8000/redoc** (alternative docs layout)

---

## API Reference

### Employee CRUD

| Method | URL | Action |
|---|---|---|
| `POST` | `/employees` | Add a new employee |
| `GET` | `/employees` | Get all employees |
| `GET` | `/employees/{id}` | Get one employee by id |
| `PUT` | `/employees/{id}` | Update an employee |
| `DELETE` | `/employees/{id}` | Delete an employee |
| `GET` | `/employees/search/query?keyword=…` | Search by name or department |

**Add employee — example request body:**

```json
{
  "name": "Alice Johnson",
  "email": "alice@example.com",
  "department": "Engineering",
  "salary": 75000.00
}
```

**Add employee — example response (201 Created):**

```json
{
  "message": "Employee created successfully",
  "id": 1
}
```

---

### Text File Operations

All files are stored inside `uploads/`.

| Method | URL | Action |
|---|---|---|
| `POST` | `/files/text/create?filename=notes.txt` | Create empty file |
| `PUT` | `/files/text/write?filename=notes.txt&content=Hello` | Write / overwrite |
| `PUT` | `/files/text/append?filename=notes.txt&content=World` | Append to file |
| `GET` | `/files/text/read?filename=notes.txt` | Read full content |
| `GET` | `/files/text/read-lines?filename=notes.txt` | Read line by line |
| `GET` | `/files/text/exists?filename=notes.txt` | Check if file exists |
| `PUT` | `/files/text/rename?old_filename=notes.txt&new_filename=new.txt` | Rename |
| `PUT` | `/files/text/copy?source_filename=notes.txt&dest_filename=copy.txt` | Copy |
| `DELETE` | `/files/text/delete?filename=notes.txt` | Delete safely |
| `GET` | `/files/text/size?filename=notes.txt` | Get size (bytes / KB / MB) |

---

### CSV Operations

| Method | URL | Action |
|---|---|---|
| `POST` | `/files/csv/import` | Upload CSV → import into MySQL |
| `GET` | `/files/csv/export` | Export MySQL → CSV in reports/ |

CSV must have this header row:
```
name,email,department,salary
```

---

### JSON Operations

| Method | URL | Action |
|---|---|---|
| `POST` | `/files/json/import` | Upload JSON array → import into MySQL |
| `GET` | `/files/json/export` | Export MySQL → JSON in reports/ |

JSON must be an array of objects:
```json
[
  {"name": "Alice", "email": "alice@example.com", "department": "Engineering", "salary": 75000}
]
```

---

### Upload and Download

| Method | URL | Action |
|---|---|---|
| `POST` | `/files/upload` | Upload .txt / .csv / .json (max 5 MB) |
| `GET` | `/files/download/upload/{filename}` | Download an uploaded file |
| `GET` | `/files/download/report/{filename}` | Download a generated report |

---

## Postman Testing Steps

1. Download and install [Postman](https://www.postman.com/downloads/)
2. Open Postman → click **New** → **Collection** → name it `Employee API`
3. For each request, click **Add a request** inside the collection

**For JSON requests (POST / PUT employees):**
- Set method → enter URL
- Go to **Body** tab → select **raw** → choose **JSON** from the dropdown
- Paste the JSON body
- Click **Send**

**For file uploads:**
- Set method to `POST` → enter the upload URL
- Go to **Body** tab → select **form-data**
- Add key: `file` → change type from Text to **File** → click **Select Files**
- Click **Send**

---

## HTTP Status Codes

| Code | Meaning | When it happens |
|---|---|---|
| 200 | OK | Successful GET, PUT, DELETE |
| 201 | Created | Successful POST (new employee added) |
| 400 | Bad Request | Invalid file extension or format |
| 404 | Not Found | Employee id or file does not exist |
| 409 | Conflict | Duplicate email address |
| 413 | Too Large | Uploaded file exceeds 5 MB |
| 422 | Unprocessable Entity | Input failed Pydantic validation |
| 503 | Service Unavailable | Cannot connect to MySQL |

---

## Common Errors and Fixes

| Error message | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'fastapi'` | Virtual env not activated | Run `.venv\Scripts\Activate.ps1` |
| `Access denied for user 'root'@'localhost'` | Wrong DB_PASSWORD in .env | Correct the password in `.env` |
| `Unknown database 'employee_db'` | Database not created yet | Run `CREATE DATABASE employee_db;` in MySQL |
| `Address already in use` | Port 8000 is occupied | Run `uvicorn main:app --reload --port 8001` |
| `422 Unprocessable Entity` | Request body is wrong | Check the JSON matches the expected schema |
| `[WinError 5] Access is denied` | File permission error | Check folder permissions on `uploads/` |
| `.venv\Scripts\Activate.ps1 cannot be loaded` | PowerShell execution policy | Run `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` |

---

## Interview Questions and Answers

**Q1. What is a REST API?**
REST (Representational State Transfer) is a design style for web APIs. Clients communicate with a server over HTTP using standard methods — GET to read, POST to create, PUT to update, DELETE to remove.

**Q2. What is the difference between PUT and PATCH?**
PUT replaces the entire resource — you must send all fields. PATCH sends only the fields you want to change (partial update).

**Q3. Why use parameterized queries (`%s`) instead of string formatting?**
String formatting like `f"INSERT INTO … VALUES ('{name}')"` allows SQL Injection. Parameterized queries let mysql-connector escape the values safely so user input cannot alter the SQL structure.

**Q4. What is the purpose of `.env` and `python-dotenv`?**
`.env` stores secrets (passwords, API keys) outside source code. `python-dotenv` loads those values into `os.environ` at startup so the code reads them with `os.getenv()`. This prevents secrets from being committed to Git.

**Q5. What does `cursor.rowcount` tell you after an UPDATE?**
It contains the number of rows actually changed. If it is 0, the `WHERE id = …` clause matched no rows — meaning that id does not exist in the table.

**Q6. What is a virtual environment and why use one?**
A virtual environment is an isolated Python installation for one project. Packages installed inside it do not affect other projects. It prevents version conflicts between different projects on the same machine.

**Q7. What is Pydantic and what does it do in FastAPI?**
Pydantic is a data validation library. FastAPI uses it to validate request bodies automatically. If the input is wrong (missing field, wrong type, negative salary), FastAPI returns a 422 error with a clear message — before the code even runs.

---

## Practice Tasks

1. Add `GET /employees/department/{dept_name}` — returns all employees in a specific department.
2. Add `PATCH /employees/{id}/salary` — updates only the salary without touching other fields.
3. Add `GET /files/text/list` — returns a list of all filenames currently in the `uploads/` folder.
4. Modify the CSV export to accept an optional `?department=Engineering` query param to filter results.
