FROM python:3.8-slim

# Install poetry
RUN pip install poetry

# Set working directory
WORKDIR /app

# Copy poetry files
COPY pyproject.toml poetry.lock ./

# Configure poetry to not create virtual environment (not needed in container)
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-dev --no-interaction --no-ansi

# Copy application code
COPY src/ ./src/

# Set environment variables
ENV PYTHONPATH=/app

# Run the cloud function
CMD ["functions-framework", "--target=archive_branches", "--port=8080"] 