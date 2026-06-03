from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="Python FastAPI Example",
    version="1.0.0",
    description="Minimal FastAPI example for Postman testing.",
)


class ExampleRequest(BaseModel):
    name: str
    message: str = ""


@app.post("/api/example")
def example(request: ExampleRequest):
    """Send a POST request from Postman with JSON: {"name": "test", "message": "hello"}"""
    return {
        "status": "success",
        "name": request.name,
        "message": request.message or f"Hello, {request.name}!",
    }
