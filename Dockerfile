# Image for Hugging Face Spaces (Docker SDK) and other container hosts.
# HF Spaces expects the app on 0.0.0.0:7860 and run as a non-root user.
# Other hosts can override the port via the PORT env var.

FROM python:3.11-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PORT=7860

RUN useradd -m -u 1000 user

# Install dependencies first (deps only, not the project package) for layer caching.
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv \
 && uv export --no-dev --no-emit-project -o /tmp/req.txt \
 && uv pip install --system -r /tmp/req.txt \
 && rm /tmp/req.txt

COPY . .
RUN chown -R user:user /app

USER user
EXPOSE 7860
# Ensure the schema is current, then serve. alembic uses DATABASE_URL/SSL from env.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
