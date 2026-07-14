FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt.

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY..

RUN pip install. && pip install pytest pytest-asyncio httpx respx

FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /app /app

COPY --from=builder /root/.cache/pip /root/.cache/pip

RUN useradd -m appuser && chown -R appuser /app

USER appuser

EXPOSE 8000

ENTRYPOINT ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
