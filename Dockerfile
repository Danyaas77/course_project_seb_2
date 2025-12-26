FROM python:3.11-slim AS deps
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"
WORKDIR /app
RUN python -m venv "$VIRTUAL_ENV" \
    && pip install --no-cache-dir --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM deps AS test
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY . .
RUN pytest -q

FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    ATTACHMENTS_DIR=/var/lib/app/attachments
WORKDIR /app
RUN groupadd --system app && useradd --system --gid app --create-home app
COPY --from=deps /opt/venv /opt/venv
COPY --chown=app:app app ./app
RUN mkdir -p /var/lib/app/attachments && chown app:app /var/lib/app/attachments
VOLUME ["/var/lib/app/attachments"]
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import sys, urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"
USER app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
