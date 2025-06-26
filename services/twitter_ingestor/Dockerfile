FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy common module first
COPY services/common /common

# Copy requirements and install dependencies
COPY services/twitter_ingestor/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install common dependencies
RUN pip install --no-cache-dir -r /common/requirements.txt

# Copy application code
COPY services/twitter_ingestor/app ./app

# Run the application
CMD ["python", "-m", "app.main"] 