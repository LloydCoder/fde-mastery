# FDE Mastery — Domain Agent Container
# Usage: docker build --build-arg DOMAIN=cybersecurity -t fde-agent:cybersecurity .

FROM python:3.11-slim

ARG DOMAIN=cybersecurity
ENV DOMAIN=${DOMAIN}
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy domain agent code
COPY month-${DOMAIN}/ /app/agent/
COPY month-7-platform/shared_orchestrator/ /app/shared_orchestrator/
COPY month-7-platform/schemas.py /app/

# API Gateway entrypoint
COPY month-7-platform/deployment/api_gateway/main.py /app/main.py

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]