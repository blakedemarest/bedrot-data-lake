FROM python:3.11-slim

# Create non-root user
RUN groupadd -r etluser && useradd -r -g etluser etluser

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory and set permissions
RUN mkdir -p logs \
    && chown -R etluser:etluser /app

# Make scripts executable
RUN chmod +x init_db.py etl_pipeline.py

# Switch to non-root user
USER etluser

# Default command
CMD ["python", "etl_pipeline.py"]