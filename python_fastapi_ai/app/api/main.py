from fastapi import FastAPI
from pydantic import BaseModel
from app.routes import llm_model_judge
from app.routes import agents_tools
from app.routes.openai import agents_tools_handoff as openai_agents_tools_handoff
from app.routes.openai import aitools_gaurdrails as openai_aitools_guardrails


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

app.include_router(llm_model_judge.router)
app.include_router(agents_tools.router)
app.include_router(openai_agents_tools_handoff.router)
app.include_router(openai_aitools_guardrails.router)