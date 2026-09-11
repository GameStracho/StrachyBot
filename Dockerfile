FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set Python path to app root
ENV PYTHONPATH=/app

# Default command (can be overridden by docker-compose)
CMD ["python", "bot/main.py"]