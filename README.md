# FastAPI Examples

A Python 3.12 FastAPI example project with a basic REST endpoint and an LLM model-judge endpoint. Dependencies and the virtual environment are managed with [uv](https://docs.astral.sh/uv/).

## What it contains

- `app/api/main.py` creates the FastAPI application and the example endpoint.
- `app/routes/llm_model_judge.py` generates an evaluation question, gets answers from OpenAI and Gemini, and asks an OpenAI model to rank them.
- `app/run.py` starts Uvicorn on `http://localhost:7000` with reload enabled.
- `app/api/llm_model_judge.py` is a standalone experimentation script; it is not imported by the web server.

## Requirements

- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Python 3.12 (uv will install it automatically when needed)
- An OpenAI API key for the model-judge endpoint
- A Google AI API key for the model-judge endpoint

## Setup

Run these commands from the project root:

```bash
uv python install 3.12
uv sync
```

`uv sync` creates `.venv` and installs the exact versions recorded in `uv.lock`.

Create a `.env` file in this directory with the keys required by the LLM comparison route:

```dotenv
OPENAI_API_KEY=your_openai_api_key
GOOGLE_API_KEY=your_google_ai_api_key
```

Do not commit `.env` or its secrets.

## Start the server

```bash
uv run python app/run.py
```

The service is available at `http://localhost:7000`; interactive OpenAPI documentation is at `http://localhost:7000/docs`.

## Endpoints

### `POST /api/example`

Send a JSON body such as:

```json
{
  "name": "test",
  "message": "hello from Postman"
}
```

The route returns the submitted name and message (or a greeting when `message` is omitted).

### `GET /api/fastapi/llm/model_judge`

This route makes API requests to OpenAI and Google Gemini, then returns the generated question, each model response, and the ranking. It needs both environment variables above and may incur provider charges.
