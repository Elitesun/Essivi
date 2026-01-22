
# Use an official Python runtime as a parent image
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV POETRY_VERSION=2.0.0

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy configuration files
COPY pyproject.toml poetry.lock* /app/

# Install dependencies
# We use --no-root because the project code isn't copied yet
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Copy project
COPY . /app/

# Expose port
EXPOSE 8000

# Run gunicorn (prod) or manage.py (dev)
# For now, we default to dev server as per plan, but use CMD to allow override
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
