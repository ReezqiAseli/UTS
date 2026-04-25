FROM python:3.11-slim

WORKDIR /app

# Non-root user setup
RUN adduser --disabled-password --gecos '' appuser && \
    mkdir -p /app/data && \
    chown -R appuser:appuser /app

USER appuser

COPY requirements.txt ./
# Dependency caching
RUN pip install --user --no-cache-dir -r requirements.txt

# Menambahkan direktori bin user ke PATH
ENV PATH="/home/appuser/.local/bin:${PATH}"

COPY src/ ./src/

EXPOSE 8080

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]