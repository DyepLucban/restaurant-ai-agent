FROM python:3.12-slim

WORKDIR /app
COPY frontend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# BACKEND_URL points at the compose network by default; override as needed
ENV BACKEND_URL=http://app:8001

CMD ["streamlit", "run", "frontend/app.py", "--server.address", "0.0.0.0", "--server.port", "8501", "--server.headless", "true"]
