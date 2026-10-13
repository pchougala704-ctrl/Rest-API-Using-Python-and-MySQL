# ─────────────────────────────────────────────────────────────
# main.py
# ─────────────────────────────────────────────────────────────
# Responsibility:
#   This is the ENTRY POINT of the application.
#   It defines every HTTP route (URL + method) and wires them
#   to the functions in employee_queries.py and file_operations.py
#
# What FastAPI does for us automatically:
#   • Parses JSON request bodies into Python objects
#   • Validates input data types (int, str, float, etc.)
#   • Returns 422 Unprocessable Entity if validation fails
#   • Generates interactive API docs at  http://127.0.0.1:8000/docs
# ─────────────────────────────────────────────────────────────

import os
import io
from pathlib import Path
from typing import Optional          # Used for optional query parameters

from fastapi import (
    FastAPI,          # The main application class
    HTTPException,    # Raises HTTP errors (404, 400, 500, …)
    UploadFile,       # Represents an uploaded file
    File,             # Used with UploadFile to mark a param as a file
    Form,             # Used to receive form-field values
    Query,            # Used for query-string parameters
    status,           # HTTP status code constants (200, 201, 404 …)
)
from fastapi.responses import FileResponse  # Stream a file back to the client
from pydantic import BaseModel, EmailStr, field_validator  # Data models + validation

from dotenv import load_dotenv

import employee_queries as eq   # All SQL functions
import file_operations  as fo   # All file-system functions
from database import create_tables   # Run CREATE TABLE IF NOT EXISTS at startup

# Load .env before anything else reads os.getenv(…)
load_dotenv()

# ── FastAPI app instance ──────────────────────────────────────
# title and description appear in the auto-generated /docs page.
app = FastAPI(
    title="Employee Management API",
    description=(
        "A beginner-friendly REST API built with FastAPI and MySQL.\n\n"
        "Covers: Employee CRUD, text files, CSV, JSON, "
        "file upload and download."
    ),
    version="1.0.0"
)


# ── Startup event ─────────────────────────────────────────────
# @app.on_event("startup") runs ONCE when uvicorn starts the app,
# before the first request arrives.  Perfect for one-time setup.
@app.on_event("startup")
def on_startup():
    """Called once when the server starts."""
    print("[main.py] Server starting — creating tables if needed …")
    create_tables()
    print("[main.py] Ready to accept requests.")


# ════════════════════════════════════════════════════════════════
# PYDANTIC MODELS  (Input validation)
# ════════════════════════════════════════════════════════════════
# A Pydantic BaseModel is a class where each attribute has a
# type annotation.  FastAPI automatically:
#   1. Reads the JSON request body
#   2. Validates each field against the declared type
#   3. Returns HTTP 422 with a clear message if validation fails
#
# This replaces manual if-not-email / if-not-number checks.
# ─────────────────────────────────────────────────────────────

class EmployeeCreate(BaseModel):
    """
    Schema for creating a new employee (POST /employees).
    All fields are required.
    """
    name:       str    # Full name — must be a non-empty string
    email:      str    # Email address
    department: str    # Department name
    salary:     float  # Monthly salary — must be a number

    # @field_validator runs AFTER the type check.
    # mode="before" means it runs on the raw input value.
    @field_validator("salary")
    @classmethod
    def salary_must_be_positive(cls, value):
        if value <= 0:
            raise ValueError("Salary must be greater than 0")
        return value

    @field_validator("name", "department")
    @classmethod
    def string_must_not_be_blank(cls, value):
        if not value.strip():
            raise ValueError("Field cannot be blank")
        return value.strip()

    @field_validator("email")
    @classmethod
    def email_must_contain_at(cls, value):
        if "@" not in value or "." not in value.split("@")[-1]:
            raise ValueError("Invalid email address")
        return value.strip().lower()


class EmployeeUpdate(BaseModel):
    """
    Schema for updating an existing employee (PUT /employees/{id}).
    Same fields as EmployeeCreate — all required for a full update.
    """
    name:       str
    email:      str
    department: str
    salary:     float

    @field_validator("salary")
    @classmethod
    def salary_must_be_positive(cls, value):
        if value <= 0:
            raise ValueError("Salary must be greater than 0")
        return value

    @field_validator("name", "department")
    @classmethod
    def string_must_not_be_blank(cls, value):
        if not value.strip():
            raise ValueError("Field cannot be blank")
        return value.strip()

    @field_validator("email")
    @classmethod
    def email_must_contain_at(cls, value):
        if "@" not in value or "." not in value.split("@")[-1]:
            raise ValueError("Invalid email address")
        return value.strip().lower()


# ════════════════════════════════════════════════════════════════
# ROOT
# ════════════════════════════════════════════════════════════════

@app.get("/", tags=["Root"])
def read_root():
    """Health-check endpoint. Visit http://127.0.0.1:8000/"""
    return {
        "message": "Employee Management API is running!",
        "docs":    "http://127.0.0.1:8000/docs"
    }


# ════════════════════════════════════════════════════════════════
# EMPLOYEE CRUD ROUTES
# ════════════════════════════════════════════════════════════════

# ── POST /employees — Add a new employee ─────────────────────
@app.post("/employees", status_code=status.HTTP_201_CREATED, tags=["Employees"])
def create_employee(employee: EmployeeCreate):
    """
    Add a new employee to the database.

    Request body (JSON):
        {
          "name": "Alice Johnson",
          "email": "alice@example.com",
          "department": "Engineering",
          "salary": 75000.00
        }

    Success response (201 Created):
        {
          "message": "Employee created successfully",
          "id": 1
        }

    Error responses:
        422 — validation failed (bad email, negative salary, etc.)
        409 — duplicate email already exists
        503 — database connection failed
    """
    result = eq.add_employee(
        name       = employee.name,
        email      = employee.email,
        department = employee.department,
        salary     = employee.salary
    )

    # Check for database-level errors
    if not result["success"]:
        error_msg = result["error"]

        # IntegrityError from MySQL contains "Duplicate entry"
        if "Duplicate" in error_msg or "duplicate" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email '{employee.email}' is already registered."
            )

        if "connection failed" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database is unavailable. Please try again later."
            )

        # Generic database error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )

    return {"message": "Employee created successfully", "id": result["id"]}


# ── GET /employees — List all employees ──────────────────────
@app.get("/employees", tags=["Employees"])
def list_employees():
    """
    Retrieve every employee from the database.

    Success response (200 OK):
        {
          "count": 2,
          "employees": [
            {"id": 1, "name": "Alice", …},
            {"id": 2, "name": "Bob",   …}
          ]
        }
    """
    employees = eq.get_all_employees()

    if employees is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not retrieve employees. Database error."
        )

    return {"count": len(employees), "employees": employees}


# ── GET /employees/{id} — Get one employee ───────────────────
@app.get("/employees/{employee_id}", tags=["Employees"])
def get_employee(employee_id: int):
    """
    Retrieve a single employee by their integer id.

    Path parameter:
        employee_id : integer (FastAPI validates this automatically)

    Success response (200 OK):
        {"id": 1, "name": "Alice", …}

    Error response:
        404 — no employee found with that id
    """
    employee = eq.get_employee_by_id(employee_id)

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with id {employee_id} not found."
        )

    return employee


# ── PUT /employees/{id} — Update an employee ─────────────────
@app.put("/employees/{employee_id}", tags=["Employees"])
def update_employee(employee_id: int, employee: EmployeeUpdate):
    """
    Update all fields of an existing employee.

    Path parameter : employee_id (integer)
    Request body   : same JSON structure as POST /employees

    Success response (200 OK):
        {"message": "Employee updated successfully"}

    Error responses:
        404 — employee not found
        409 — new email is already used by another employee
    """
    result = eq.update_employee(
        employee_id = employee_id,
        name        = employee.name,
        email       = employee.email,
        department  = employee.department,
        salary      = employee.salary
    )

    if not result["success"]:
        error_msg = result["error"]
        if "Duplicate" in error_msg or "duplicate" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email '{employee.email}' is already taken."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )

    # rows_affected == 0 means the id did not exist in the table
    if result["rows_affected"] == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with id {employee_id} not found."
        )

    return {"message": "Employee updated successfully"}


# ── DELETE /employees/{id} — Delete an employee ──────────────
@app.delete("/employees/{employee_id}", tags=["Employees"])
def delete_employee(employee_id: int):
    """
    Delete an employee by id.

    Success response (200 OK):
        {"message": "Employee deleted successfully"}

    Error response:
        404 — employee not found
    """
    result = eq.delete_employee(employee_id)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["error"]
        )

    if result["rows_affected"] == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with id {employee_id} not found."
        )

    return {"message": "Employee deleted successfully"}


# ── GET /employees/search — Search by name or department ─────
@app.get("/employees/search/query", tags=["Employees"])
def search_employees(
    keyword: str = Query(..., min_length=1, description="Name or department keyword")
):
    """
    Search employees by name or department (partial match).

    Query parameter:
        keyword : e.g. /employees/search/query?keyword=eng

    Success response (200 OK):
        {
          "count": 3,
          "results": [{"id": 2, "name": "Bob", "department": "Engineering", …}, …]
        }
    """
    results = eq.search_employees(keyword)

    if results is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Search failed. Database error."
        )

    return {"count": len(results), "results": results}


# ════════════════════════════════════════════════════════════════
# TEXT FILE ROUTES
# ════════════════════════════════════════════════════════════════

@app.post("/files/text/create", tags=["Text Files"])
def create_file(filename: str = Query(..., description="e.g. notes.txt")):
    """
    Create an empty text file in the uploads folder.

    Query param: filename=notes.txt
    """
    result = fo.create_text_file(filename)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.put("/files/text/write", tags=["Text Files"])
def write_file(
    filename: str  = Query(...),
    content:  str  = Query(..., description="Content to write (replaces existing)")
):
    """Write (overwrite) content to a text file."""
    result = fo.write_text_file(filename, content)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.put("/files/text/append", tags=["Text Files"])
def append_file(
    filename: str = Query(...),
    content:  str = Query(..., description="Content to append")
):
    """Append content to an existing text file."""
    result = fo.append_text_file(filename, content)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/files/text/read", tags=["Text Files"])
def read_file_full(filename: str = Query(...)):
    """Read the entire content of a text file."""
    result = fo.read_text_file(filename)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/files/text/read-lines", tags=["Text Files"])
def read_file_lines(filename: str = Query(...)):
    """Read a text file line by line."""
    result = fo.read_file_line_by_line(filename)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/files/text/exists", tags=["Text Files"])
def check_file_exists(filename: str = Query(...)):
    """Check if a file exists in the uploads folder."""
    return fo.file_exists(filename)


@app.put("/files/text/rename", tags=["Text Files"])
def rename_file(
    old_filename: str = Query(...),
    new_filename: str = Query(...)
):
    """Rename a file inside the uploads folder."""
    result = fo.rename_file(old_filename, new_filename)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.put("/files/text/copy", tags=["Text Files"])
def copy_file(
    source_filename: str = Query(...),
    dest_filename:   str = Query(...)
):
    """Copy a file within the uploads folder."""
    result = fo.copy_file(source_filename, dest_filename)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.delete("/files/text/delete", tags=["Text Files"])
def delete_file(filename: str = Query(...)):
    """Delete a file from the uploads folder."""
    result = fo.delete_text_file(filename)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/files/text/size", tags=["Text Files"])
def file_size(filename: str = Query(...)):
    """Return the size of a file in bytes, KB, and MB."""
    result = fo.get_file_size(filename)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ════════════════════════════════════════════════════════════════
# CSV ROUTES
# ════════════════════════════════════════════════════════════════

@app.post("/files/csv/import", tags=["CSV Files"])
async def import_csv(file: UploadFile = File(...)):
    """
    Upload a CSV file and import valid rows into MySQL.

    The CSV must have a header row:
        name,email,department,salary

    The API:
        1. Validates the file extension
        2. Reads and validates every row
        3. Bulk-inserts valid rows into MySQL
        4. Reports inserted count and skipped (invalid/duplicate) count

    Use Postman → Body → form-data → key=file, type=File
    """
    # ── Validate file extension ───────────────────────────────
    max_size  = int(os.getenv("MAX_FILE_SIZE", 5242880))
    file_ext  = Path(file.filename).suffix.lower()

    if file_ext != ".csv":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .csv files are accepted for this endpoint."
        )

    # ── Read file bytes ───────────────────────────────────────
    content = await file.read()   # await because this is async I/O

    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {max_size // (1024*1024)} MB."
        )

    # ── Save temporarily so we can pass a Path to read_csv_file ─
    temp_path = fo.UPLOAD_DIR / f"_temp_{file.filename}"
    temp_path.write_bytes(content)

    try:
        # Parse and validate the CSV rows
        csv_result = fo.read_csv_file(temp_path)

        if not csv_result["success"]:
            raise HTTPException(status_code=400, detail=csv_result["error"])

        valid_rows   = csv_result["valid_rows"]
        invalid_rows = csv_result["invalid_rows"]

        # Insert valid rows into MySQL
        if valid_rows:
            insert_result = eq.bulk_insert_employees(valid_rows)
        else:
            insert_result = {"success": True, "inserted": 0, "skipped": 0}

        return {
            "message":         "CSV import complete",
            "rows_in_file":    len(valid_rows) + len(invalid_rows),
            "valid_rows":      len(valid_rows),
            "invalid_rows":    invalid_rows,
            "db_inserted":     insert_result.get("inserted", 0),
            "db_skipped_dup":  insert_result.get("skipped", 0)
        }

    finally:
        # Always remove the temp file, even if an error occurred
        if temp_path.exists():
            temp_path.unlink()


@app.get("/files/csv/export", tags=["CSV Files"])
def export_csv():
    """
    Export all employees from MySQL to a CSV file in reports/.

    Returns a download link for the generated file.

    Success response:
        {
          "message": "CSV exported",
          "download_url": "/files/download/report/employees_export.csv",
          "rows": 42
        }
    """
    employees = eq.get_employees_for_export()

    if employees is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not fetch employees from database."
        )

    report_path = fo.REPORTS_DIR / "employees_export.csv"
    result      = fo.write_csv_file(report_path, employees)

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])

    return {
        "message":      "CSV export complete",
        "download_url": "/files/download/report/employees_export.csv",
        "rows":         result["rows_written"]
    }


# ════════════════════════════════════════════════════════════════
# JSON ROUTES
# ════════════════════════════════════════════════════════════════

@app.post("/files/json/import", tags=["JSON Files"])
async def import_json(file: UploadFile = File(...)):
    """
    Upload a JSON file containing an array of employee objects and
    insert valid records into MySQL.

    Expected JSON format:
        [
          {"name": "Alice", "email": "alice@example.com",
           "department": "Engineering", "salary": 75000},
          …
        ]

    Postman → Body → form-data → key=file, type=File
    """
    max_size = int(os.getenv("MAX_FILE_SIZE", 5242880))
    file_ext = Path(file.filename).suffix.lower()

    if file_ext != ".json":
        raise HTTPException(
            status_code=400,
            detail="Only .json files are accepted for this endpoint."
        )

    content = await file.read()

    if len(content) > max_size:
        raise HTTPException(status_code=413, detail="File too large.")

    # Save temp file
    temp_path = fo.UPLOAD_DIR / f"_temp_{file.filename}"
    temp_path.write_bytes(content)

    try:
        json_result = fo.read_json_file(temp_path)

        if not json_result["success"]:
            raise HTTPException(status_code=400, detail=json_result["error"])

        data = json_result["data"]

        # Validate that the JSON root is a list
        if not isinstance(data, list):
            raise HTTPException(
                status_code=400,
                detail="JSON must be an array (list) of employee objects."
            )

        # Validate each item and separate valid from invalid
        valid_rows   = []
        invalid_rows = []

        for i, item in enumerate(data):
            reason = _validate_json_employee(item, i + 1)
            if reason:
                invalid_rows.append({"index": i + 1, "data": item, "reason": reason})
            else:
                valid_rows.append({
                    "name":       str(item["name"]).strip(),
                    "email":      str(item["email"]).strip().lower(),
                    "department": str(item["department"]).strip(),
                    "salary":     float(item["salary"])
                })

        insert_result = eq.bulk_insert_employees(valid_rows) if valid_rows else {
            "success": True, "inserted": 0, "skipped": 0
        }

        return {
            "message":        "JSON import complete",
            "total":          len(data),
            "valid":          len(valid_rows),
            "invalid":        invalid_rows,
            "db_inserted":    insert_result.get("inserted", 0),
            "db_skipped_dup": insert_result.get("skipped", 0)
        }

    finally:
        if temp_path.exists():
            temp_path.unlink()


def _validate_json_employee(item: dict, index: int) -> str:
    """
    Validate a single JSON employee object.
    Returns error string or "" if valid.
    """
    if not isinstance(item, dict):
        return "Item is not a JSON object"

    for key in ("name", "email", "department", "salary"):
        if key not in item:
            return f"Missing field '{key}'"

    if not str(item.get("name", "")).strip():
        return "Name is empty"

    email = str(item.get("email", ""))
    if "@" not in email or "." not in email.split("@")[-1]:
        return "Email is invalid"

    try:
        salary = float(item["salary"])
        if salary < 0:
            return "Salary cannot be negative"
    except (ValueError, TypeError):
        return "Salary is not a valid number"

    return ""


@app.get("/files/json/export", tags=["JSON Files"])
def export_json():
    """
    Export all employees from MySQL to a JSON file in reports/.

    Returns a download link for the generated file.
    """
    employees = eq.get_employees_for_export()

    if employees is None:
        raise HTTPException(
            status_code=503,
            detail="Could not fetch employees from database."
        )

    report_path = fo.REPORTS_DIR / "employees_export.json"
    result      = fo.write_json_file(report_path, employees)

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])

    return {
        "message":      "JSON export complete",
        "download_url": "/files/download/report/employees_export.json",
        "records":      len(employees)
    }


# ════════════════════════════════════════════════════════════════
# UPLOAD & DOWNLOAD ROUTES
# ════════════════════════════════════════════════════════════════

@app.post("/files/upload", tags=["Upload & Download"])
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a text, CSV, or JSON file to the uploads folder.

    Validates:
        • Extension must be .txt, .csv, or .json
        • Size must not exceed MAX_FILE_SIZE (default 5 MB)

    Postman:
        POST http://127.0.0.1:8000/files/upload
        Body → form-data → key: file  (type: File) → select your file

    Success response (200 OK):
        {
          "message": "File uploaded successfully",
          "filename": "employees.csv",
          "size_bytes": 1024,
          "download_url": "/files/download/upload/employees.csv"
        }
    """
    max_size = int(os.getenv("MAX_FILE_SIZE", 5242880))
    content  = await file.read()

    # Validate extension and size BEFORE saving to disk
    validation = fo.validate_upload_file(file.filename, len(content), max_size)
    if not validation["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation["error"]
        )

    save_result = fo.save_uploaded_file(file.filename, content)
    if not save_result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=save_result["error"]
        )

    return {
        "message":      "File uploaded successfully",
        "filename":     file.filename,
        "size_bytes":   save_result["size_bytes"],
        "download_url": f"/files/download/upload/{file.filename}"
    }


@app.get("/files/download/upload/{filename}", tags=["Upload & Download"])
def download_uploaded_file(filename: str):
    """
    Download a file from the uploads folder.

    Path parameter: filename
    Example: GET /files/download/upload/employees.csv

    FastAPI's FileResponse streams the file directly to the client.
    It sets Content-Disposition: attachment so the browser downloads
    the file instead of trying to display it.

    Error: 404 if the file does not exist.
    """
    path = fo.get_upload_path(filename)

    if path is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File '{filename}' not found in uploads folder."
        )

    # FileResponse(path) → FastAPI streams the file bytes
    # media_type="application/octet-stream" is a safe default for
    # binary downloads; the browser will show a Save As dialog.
    return FileResponse(
        path       = str(path),
        filename   = filename,
        media_type = "application/octet-stream"
    )


@app.get("/files/download/report/{filename}", tags=["Upload & Download"])
def download_report_file(filename: str):
    """
    Download a generated report (CSV or JSON) from the reports folder.

    Path parameter: filename
    Example: GET /files/download/report/employees_export.csv

    Error: 404 if the file does not exist.
    """
    path = fo.get_report_path(filename)

    if path is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report '{filename}' not found. Run an export first."
        )

    return FileResponse(
        path       = str(path),
        filename   = filename,
        media_type = "application/octet-stream"
    )
