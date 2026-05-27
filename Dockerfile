FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml README.md requirements*.txt /app/
COPY src /app/src
COPY sample_data /app/sample_data
COPY prompts /app/prompts

RUN python -m pip install --upgrade pip \
    && python -m pip install --no-cache-dir -e ".[api]"

EXPOSE 8000
CMD ["uvicorn", "gq_insight_copilot.api:app", "--host", "0.0.0.0", "--port", "8000"]
