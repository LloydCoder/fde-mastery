FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN useradd --create-home --uid 10001 appuser
WORKDIR /app

COPY pyproject.toml ./
COPY schemas.py domain_agent.py observability_metrics.py config.py ./
COPY observability ./observability
COPY deployment ./deployment
COPY persistence ./persistence
COPY shared_orchestrator ./shared_orchestrator
COPY integrations ./integrations
COPY security ./security
COPY api.py ./api.py

RUN pip install --no-cache-dir --upgrade pip "setuptools>=83.0.0" \
    && pip install --no-cache-dir ".[redis,observability]"

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"

CMD ["uvicorn", "deployment.api_gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]
