# Python FastAPI Example

Minimal FastAPI REST example for testing with Postman.

## Setup

```bash
cd python_fastapi_ai
pip install -r requirements.txt
```

## Run

```bash
cd app
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
