FROM python:3.12-slim AS builder

WORKDIR /app
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]