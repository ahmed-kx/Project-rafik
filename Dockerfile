# Dockerfile - builds the image for the WEB APP only.
# PostgreSQL is NOT built here: it uses the official image in docker-compose.yml.

# Slim Python image: much smaller than the full one, so faster to build and pull.
FROM python:3.12-slim

# All following commands run inside /app in the container.
WORKDIR /app

# Copy requirements.txt first and install. Docker caches this layer, so
# rebuilding after a code change does not reinstall every package.
COPY requirements.txt .
# --no-cache-dir keeps the image smaller.
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the application code (.dockerignore excludes .env and other files).
COPY . .

# Run as a normal user instead of root: safer if the app is ever compromised.
RUN useradd --create-home appuser
USER appuser

# Documentation only: the app listens on port 5000 inside the container.
# The port is really published in docker-compose.yml.
EXPOSE 5000

# gunicorn is a real production server (Flask's built-in server is for testing).
# --bind 0.0.0.0 : listen on all interfaces, otherwise the host cannot reach it.
# --workers 1 --threads 4 : one process, so the "create tables" step at startup
#   runs only once (several workers could run it at the same time).
# app:app : file app.py, variable app.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "4", "app:app"]
