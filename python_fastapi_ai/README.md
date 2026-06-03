# Python FastAPI Example

Minimal FastAPI REST example for testing with Postman.

## Setup

From the repo root (`D:\my_personal\python_fastapi_ai`):

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r python_fastapi_ai\requirements.txt
```

**Important (Windows):** Do not use `pip install ...` directly. On many Windows machines it fails with `Access is denied`. Always use:

```powershell
python -m pip install -r python_fastapi_ai\requirements.txt
```

## Run

```powershell
cd python_fastapi_ai\app
python run.py
```

Server runs at `http://localhost:7000`.

## Test with Postman

- **Method:** POST
- **URL:** `http://localhost:7000/api/example`
- **Headers:** `Content-Type: application/json`
- **Body (raw JSON):**

```json
{
  "name": "test",
  "message": "hello from Postman"
}
```

Interactive API docs: `http://localhost:7000/docs`
