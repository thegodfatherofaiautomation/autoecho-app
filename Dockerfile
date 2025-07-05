# Use an official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy rest of app
COPY . .

# Set env port
ENV PORT=8080

# Expose and run
EXPOSE 8080
CMD ["python", "app.py"]
