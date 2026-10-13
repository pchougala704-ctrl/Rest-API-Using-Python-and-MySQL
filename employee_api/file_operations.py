# ─────────────────────────────────────────────────────────────
# file_operations.py
# ─────────────────────────────────────────────────────────────
# Responsibility:
#   All file-system operations live here:
#     • Text files  (create, write, append, read, rename, copy, delete)
#     • CSV files   (read, validate, write)
#     • JSON files  (read, write, validate)
#     • Upload/download helpers (safe path resolution)
#
# SECURITY NOTE:
#   Every function that accepts a filename checks it against the
#   allowed folder using _safe_path().  This prevents "path
#   traversal" attacks where a user sends a filename like
#   "../../etc/passwd" to read system files.
# ─────────────────────────────────────────────────────────────

import os          # os.path, os.rename, os.remove, os.getcwd …
import csv         # Built-in CSV reader/writer
import json        # Built-in JSON encoder/decoder
import shutil      # High-level file operations (copy, move)

from pathlib import Path  # Modern, readable path handling


# ── Base directories (resolved relative to this file's location) ─
# Path(__file__).parent → the folder that contains file_operations.py
#                         i.e.  …/employee_api/
BASE_DIR     = Path(__file__).parent
UPLOAD_DIR   = BASE_DIR / "uploads"    # Where uploaded files are saved
REPORTS_DIR  = BASE_DIR / "reports"   # Where generated reports are saved

# Ensure both directories exist when this module is first imported
UPLOAD_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

# Allowed file extensions for uploads (lowercase)
ALLOWED_EXTENSIONS = {".txt", ".csv", ".json"}


# ════════════════════════════════════════════════════════════════
# SECURITY HELPER — _safe_path()
# ════════════════════════════════════════════════════════════════
def _safe_path(folder: Path, filename: str) -> Path:
    """
    Build a full path and verify it stays inside 'folder'.

    Why this matters:
        If filename = "../../etc/passwd", then
        folder / filename  resolves to  /etc/passwd
        which is OUTSIDE the allowed folder.
        resolve() expands all ".." and symlinks to an absolute path.
        We then check that the result starts with the folder's absolute
        path.  If not, we raise a ValueError to reject the request.

    Args:
        folder   : The allowed base directory (Path object)
        filename : The user-supplied filename string

    Returns:
        Path object pointing to the safe full path

    Raises:
        ValueError if the path escapes the allowed folder
    """
    # Strip any directory separators the user might have prepended
    # os.path.basename("../../etc/passwd") → "passwd"
    clean_filename = os.path.basename(filename)

    full_path = (folder / clean_filename).resolve()
    allowed   = folder.resolve()

    # str(full_path).startswith(str(allowed)) verifies containment
    if not str(full_path).startswith(str(allowed)):
        raise ValueError(f"Access denied: '{filename}' is outside the allowed folder.")

    return full_path


# ════════════════════════════════════════════════════════════════
# TEXT FILE OPERATIONS
# ════════════════════════════════════════════════════════════════

def create_text_file(filename: str) -> dict:
    """
    Create an empty text file in the uploads folder.

    If the file already exists it is NOT overwritten — we return
    a message saying it already exists.

    Args:
        filename : e.g. "notes.txt"

    Returns:
        {"success": True, "path": "…"}  OR
        {"success": False, "error": "…"}
    """
    try:
        path = _safe_path(UPLOAD_DIR, filename)

        if path.exists():
            return {"success": False, "error": f"File '{filename}' already exists."}

        # "x" mode creates the file and fails if it exists.
        # encoding="utf-8" ensures consistent text encoding on all OS.
        with open(path, "x", encoding="utf-8") as f:
            pass  # We just want an empty file — nothing to write yet

        return {"success": True, "path": str(path)}

    except ValueError as e:
        return {"success": False, "error": str(e)}
    except OSError as e:
        # OSError covers permission errors, disk full, etc.
        return {"success": False, "error": f"OS error: {e}"}


def write_text_file(filename: str, content: str) -> dict:
    """
    Write content to a file, REPLACING any existing content.

    "w" mode truncates (empties) the file before writing.
    If the file does not exist, it is created automatically.

    Args:
        filename : Target filename inside uploads/
        content  : String to write

    Returns:
        {"success": True, "bytes_written": N}  OR
        {"success": False, "error": "…"}
    """
    try:
        path = _safe_path(UPLOAD_DIR, filename)

        with open(path, "w", encoding="utf-8") as f:
            bytes_written = f.write(content)

        return {"success": True, "bytes_written": bytes_written}

    except ValueError as e:
        return {"success": False, "error": str(e)}
    except OSError as e:
        return {"success": False, "error": f"OS error: {e}"}


def append_text_file(filename: str, content: str) -> dict:
    """
    Append content to an existing file WITHOUT erasing what is there.

    "a" mode positions the write cursor at the END of the file.
    If the file does not exist, it is created.

    Args:
        filename : Target filename inside uploads/
        content  : String to append

    Returns:
        {"success": True, "bytes_appended": N}  OR
        {"success": False, "error": "…"}
    """
    try:
        path = _safe_path(UPLOAD_DIR, filename)

        with open(path, "a", encoding="utf-8") as f:
            bytes_appended = f.write(content)

        return {"success": True, "bytes_appended": bytes_appended}

    except ValueError as e:
        return {"success": False, "error": str(e)}
    except OSError as e:
        return {"success": False, "error": f"OS error: {e}"}


def read_text_file(filename: str) -> dict:
    """
    Read the entire content of a text file as a single string.

    "r" mode (the default) opens for reading.
    f.read() loads the entire file into memory at once.
    Good for small files; for large files use read_file_line_by_line().

    Returns:
        {"success": True, "content": "…"}  OR
        {"success": False, "error": "…"}
    """
    try:
        path = _safe_path(UPLOAD_DIR, filename)

        if not path.exists():
            return {"success": False, "error": f"File '{filename}' not found."}

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        return {"success": True, "content": content}

    except ValueError as e:
        return {"success": False, "error": str(e)}
    except OSError as e:
        return {"success": False, "error": f"OS error: {e}"}


def read_file_line_by_line(filename: str) -> dict:
    """
    Read a file line by line and return a list of lines.

    f.readlines() returns a list where each element is one line
    including the newline character '\\n'.
    We strip() each line to remove trailing whitespace/newlines.

    Useful when the file is large and you only want to process
    one line at a time (memory-efficient).

    Returns:
        {"success": True, "lines": ["line1", "line2", …]}  OR
        {"success": False, "error": "…"}
    """
    try:
        path = _safe_path(UPLOAD_DIR, filename)

        if not path.exists():
            return {"success": False, "error": f"File '{filename}' not found."}

        lines = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:                   # Iterating the file object reads line-by-line
                lines.append(line.rstrip())  # rstrip() removes trailing \n and spaces

        return {"success": True, "lines": lines, "total_lines": len(lines)}

    except ValueError as e:
        return {"success": False, "error": str(e)}
    except OSError as e:
        return {"success": False, "error": f"OS error: {e}"}


def file_exists(filename: str) -> dict:
    """
    Check if a file exists in the uploads folder.

    path.exists() returns True if the path points to any existing
    file-system entry (file OR directory).
    path.is_file() is more specific — only True for regular files.

    Returns:
        {"exists": True/False, "path": "…"}
    """
    try:
        path = _safe_path(UPLOAD_DIR, filename)
        return {"exists": path.is_file(), "path": str(path)}

    except ValueError as e:
        return {"exists": False, "error": str(e)}


def rename_file(old_filename: str, new_filename: str) -> dict:
    """
    Rename a file inside the uploads folder.

    Both old and new paths are safety-checked so a user cannot
    rename a file OUTSIDE the uploads folder.

    os.rename(src, dst) — built-in rename (same drive only on Windows)
    path.rename(target) — pathlib equivalent (cross-platform)

    Returns:
        {"success": True, "new_path": "…"}  OR
        {"success": False, "error": "…"}
    """
    try:
        old_path = _safe_path(UPLOAD_DIR, old_filename)
        new_path = _safe_path(UPLOAD_DIR, new_filename)

        if not old_path.exists():
            return {"success": False, "error": f"File '{old_filename}' not found."}

        if new_path.exists():
            return {"success": False, "error": f"File '{new_filename}' already exists."}

        old_path.rename(new_path)  # Atomic rename on most OS
        return {"success": True, "new_path": str(new_path)}

    except ValueError as e:
        return {"success": False, "error": str(e)}
    except OSError as e:
        return {"success": False, "error": f"OS error: {e}"}


def copy_file(source_filename: str, dest_filename: str) -> dict:
    """
    Copy a file within the uploads folder.

    shutil.copy2(src, dst) copies both the file content AND the
    metadata (timestamps).  shutil.copy() copies content only.

    Returns:
        {"success": True, "destination": "…"}  OR
        {"success": False, "error": "…"}
    """
    try:
        src  = _safe_path(UPLOAD_DIR, source_filename)
        dest = _safe_path(UPLOAD_DIR, dest_filename)

        if not src.exists():
            return {"success": False, "error": f"Source file '{source_filename}' not found."}

        shutil.copy2(str(src), str(dest))
        return {"success": True, "destination": str(dest)}

    except ValueError as e:
        return {"success": False, "error": str(e)}
    except OSError as e:
        return {"success": False, "error": f"OS error: {e}"}


def delete_text_file(filename: str) -> dict:
    """
    Safely delete a file from the uploads folder.

    os.remove() raises FileNotFoundError if the file does not exist,
    so we check first.

    We NEVER allow filenames like "../../important.py".
    _safe_path() blocks those attempts.

    Returns:
        {"success": True}  OR
        {"success": False, "error": "…"}
    """
    try:
        path = _safe_path(UPLOAD_DIR, filename)

        if not path.exists():
            return {"success": False, "error": f"File '{filename}' not found."}

        os.remove(path)  # Delete the file
        return {"success": True, "message": f"File '{filename}' deleted."}

    except ValueError as e:
        return {"success": False, "error": str(e)}
    except OSError as e:
        return {"success": False, "error": f"OS error: {e}"}


def get_file_size(filename: str) -> dict:
    """
    Return the size of a file in bytes.

    os.path.getsize() returns an integer number of bytes.
    We also calculate KB and MB for human readability.

    Returns:
        {"success": True, "bytes": N, "kilobytes": K, "megabytes": M}  OR
        {"success": False, "error": "…"}
    """
    try:
        path = _safe_path(UPLOAD_DIR, filename)

        if not path.exists():
            return {"success": False, "error": f"File '{filename}' not found."}

        size_bytes = os.path.getsize(path)
        return {
            "success":    True,
            "filename":   filename,
            "bytes":      size_bytes,
            "kilobytes":  round(size_bytes / 1024, 2),
            "megabytes":  round(size_bytes / (1024 * 1024), 4)
        }

    except ValueError as e:
        return {"success": False, "error": str(e)}
    except OSError as e:
        return {"success": False, "error": f"OS error: {e}"}


# ════════════════════════════════════════════════════════════════
# CSV FILE OPERATIONS
# ════════════════════════════════════════════════════════════════

# Expected columns in a valid CSV employee file
REQUIRED_CSV_COLUMNS = {"name", "email", "department", "salary"}


def read_csv_file(filepath: Path) -> dict:
    """
    Read and VALIDATE a CSV file of employee records.

    The CSV must have a header row with (at minimum):
        name, email, department, salary

    Row validation:
        • All required columns present
        • salary is a valid positive number
        • name and email are non-empty strings

    Args:
        filepath : Full Path object to the CSV file

    Returns:
        {
          "success": True,
          "valid_rows": [{"name": …, "email": …, …}, …],
          "invalid_rows": [{"row_number": N, "data": {…}, "reason": "…"}, …]
        }
    """
    valid_rows   = []
    invalid_rows = []

    try:
        with open(filepath, "r", encoding="utf-8", newline="") as f:
            # csv.DictReader reads the first row as column headers
            # and returns each subsequent row as a dict.
            reader = csv.DictReader(f)

            # Check that all required columns are present in the header
            if not REQUIRED_CSV_COLUMNS.issubset(set(reader.fieldnames or [])):
                missing = REQUIRED_CSV_COLUMNS - set(reader.fieldnames or [])
                return {
                    "success": False,
                    "error": f"Missing columns: {missing}"
                }

            for row_number, row in enumerate(reader, start=2):  # start=2: row 1 is header
                reason = _validate_csv_row(row)
                if reason:
                    invalid_rows.append({
                        "row_number": row_number,
                        "data":       dict(row),
                        "reason":     reason
                    })
                else:
                    valid_rows.append({
                        "name":       row["name"].strip(),
                        "email":      row["email"].strip(),
                        "department": row["department"].strip(),
                        "salary":     float(row["salary"])
                    })

        return {
            "success":      True,
            "valid_rows":   valid_rows,
            "invalid_rows": invalid_rows
        }

    except FileNotFoundError:
        return {"success": False, "error": "CSV file not found."}
    except OSError as e:
        return {"success": False, "error": f"OS error: {e}"}


def _validate_csv_row(row: dict) -> str:
    """
    Validate a single CSV row.

    Returns an error reason string if invalid, or "" if valid.
    Private helper (name starts with _) — not called from outside.
    """
    name       = row.get("name", "").strip()
    email      = row.get("email", "").strip()
    department = row.get("department", "").strip()
    salary_str = row.get("salary", "").strip()

    if not name:
        return "Name is empty"
    if not email or "@" not in email:
        return "Email is invalid"
    if not department:
        return "Department is empty"
    try:
        salary = float(salary_str)
        if salary < 0:
            return "Salary cannot be negative"
    except ValueError:
        return f"Salary '{salary_str}' is not a number"

    return ""  # No error → row is valid


def write_csv_file(filepath: Path, employees: list) -> dict:
    """
    Write a list of employee dicts to a CSV file.

    csv.DictWriter takes a list of fieldnames and writes a header
    row automatically via writeheader().

    Args:
        filepath  : Full Path object to the destination CSV
        employees : List of dicts with keys id, name, email,
                    department, salary

    Returns:
        {"success": True, "rows_written": N}  OR
        {"success": False, "error": "…"}
    """
    fieldnames = ["id", "name", "email", "department", "salary"]

    try:
        with open(filepath, "w", encoding="utf-8", newline="") as f:
            # newline="" is important for CSV on Windows — without it,
            # the writer adds an extra blank line between every row.
            writer = csv.DictWriter(f, fieldnames=fieldnames,
                                    extrasaction="ignore")
            writer.writeheader()          # Writes the column names row
            writer.writerows(employees)   # Writes all data rows at once

        return {"success": True, "rows_written": len(employees)}

    except OSError as e:
        return {"success": False, "error": f"OS error: {e}"}


# ════════════════════════════════════════════════════════════════
# JSON FILE OPERATIONS
# ════════════════════════════════════════════════════════════════

def read_json_file(filepath: Path) -> dict:
    """
    Read and parse a JSON file.

    json.load(f) parses the entire file as a JSON value.
    If the content is invalid JSON, it raises json.JSONDecodeError.

    Args:
        filepath : Full Path object to the JSON file

    Returns:
        {"success": True, "data": <parsed Python object>}  OR
        {"success": False, "error": "…"}
    """
    try:
        if not filepath.exists():
            return {"success": False, "error": "JSON file not found."}

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)  # Parses JSON → Python dict/list

        return {"success": True, "data": data}

    except json.JSONDecodeError as e:
        # JSONDecodeError gives us the line and column where the
        # parsing failed, which is very useful for debugging.
        return {"success": False, "error": f"Invalid JSON: {e}"}
    except OSError as e:
        return {"success": False, "error": f"OS error: {e}"}


def write_json_file(filepath: Path, data) -> dict:
    """
    Serialize a Python object (dict or list) to a JSON file.

    json.dump(data, f, indent=4) writes pretty-printed JSON.
    indent=4 adds 4 spaces of indentation per nesting level,
    making the file human-readable.

    default=str handles types like Decimal and datetime that are
    not natively JSON-serializable by converting them to strings.

    Args:
        filepath : Full Path object to the destination JSON file
        data     : Python dict or list to serialize

    Returns:
        {"success": True, "path": "…"}  OR
        {"success": False, "error": "…"}
    """
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, default=str)

        return {"success": True, "path": str(filepath)}

    except (TypeError, ValueError) as e:
        # TypeError   → data contains something not JSON-serializable
        # ValueError  → rare, but possible with certain edge cases
        return {"success": False, "error": f"Serialization error: {e}"}
    except OSError as e:
        return {"success": False, "error": f"OS error: {e}"}


# ════════════════════════════════════════════════════════════════
# UPLOAD / DOWNLOAD HELPERS
# ════════════════════════════════════════════════════════════════

def validate_upload_file(filename: str, file_size: int, max_size: int) -> dict:
    """
    Validate a file before saving it to disk.

    Checks:
        1. Extension must be in ALLOWED_EXTENSIONS
        2. File size must not exceed max_size bytes

    Args:
        filename  : Original filename from the upload
        file_size : Size in bytes
        max_size  : Maximum allowed bytes (from .env MAX_FILE_SIZE)

    Returns:
        {"valid": True}  OR
        {"valid": False, "error": "…"}
    """
    # Path(filename).suffix returns the extension including the dot
    # e.g. "report.csv" → ".csv"
    ext = Path(filename).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(ALLOWED_EXTENSIONS)
        return {
            "valid": False,
            "error": f"Extension '{ext}' not allowed. Allowed: {allowed}"
        }

    if file_size > max_size:
        max_mb = round(max_size / (1024 * 1024), 2)
        return {
            "valid": False,
            "error": f"File exceeds maximum size of {max_mb} MB."
        }

    return {"valid": True}


def save_uploaded_file(filename: str, content: bytes) -> dict:
    """
    Save raw bytes to the uploads folder.

    Args:
        filename : Target filename (will be sanitised by _safe_path)
        content  : Raw bytes from the upload

    Returns:
        {"success": True, "saved_path": "…", "size_bytes": N}  OR
        {"success": False, "error": "…"}
    """
    try:
        path = _safe_path(UPLOAD_DIR, filename)

        # "wb" = write binary mode.  We use binary because the file
        # content might not be plain text (e.g., it could be a CSV
        # with a BOM marker).  Writing raw bytes avoids encoding issues.
        with open(path, "wb") as f:
            f.write(content)

        return {
            "success":    True,
            "saved_path": str(path),
            "size_bytes": len(content)
        }

    except ValueError as e:
        return {"success": False, "error": str(e)}
    except OSError as e:
        return {"success": False, "error": f"OS error: {e}"}


def get_upload_path(filename: str) -> Path | None:
    """
    Resolve the full path of an uploaded file for download.

    Returns the Path if the file exists, None otherwise.
    The caller (main.py) uses this to pass the path to FastAPI's
    FileResponse, which streams the file back to the client.
    """
    try:
        path = _safe_path(UPLOAD_DIR, filename)
        return path if path.is_file() else None

    except ValueError:
        return None


def get_report_path(filename: str) -> Path | None:
    """
    Resolve the full path of a generated report file for download.

    Same as get_upload_path() but looks in the reports/ folder.
    """
    try:
        path = _safe_path(REPORTS_DIR, filename)
        return path if path.is_file() else None

    except ValueError:
        return None
