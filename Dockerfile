# Dockerfile

FROM python:3.12.7-slim

# Set working directory
WORKDIR /app

# Install system dependencies (needed for mysql-connector-python)
# Install required system dependencies
RUN apt-get update && apt-get install -y \
    pkg-config \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*
    
# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy the entire app
COPY . .

# Expose FastAPI app port
EXPOSE 8800

# Start the FastAPI app with Uvicorn
CMD ["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8800"]
