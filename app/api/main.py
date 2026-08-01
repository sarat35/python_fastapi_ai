from fastapi import FastAPI
from pydantic import BaseModel
from routes import llm_model_judge

app = FastAPI(
    title="FastAPI Examples",
    version="1.0.0",
    description="Basic REST and LLM model-judge FastAPI examples.",
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

app.include_router(llm_model_judge.router)
