# RMP API

A FastAPI wrapper around Rate My Professors data.

## Setup

This project uses `uv` as the package manager. To get started:

1. Install uv:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Create and activate a virtual environment:

```bash
uv venv
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate  # On Windows
```

3. Install dependencies:

```bash
uv pip install .
```

## Development

For development, install in editable mode:

```bash
uv pip install -e .
```

## Running the API

```bash
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

API documentation will be available at:

- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)
