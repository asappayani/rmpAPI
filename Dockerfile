FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Copy dependency files
COPY pyproject.toml .

# Install dependencies using uv
RUN uv pip install .

# Copy the rest of the application
COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 