# Use the official Python image
FROM python:3.10-slim

# Set environment vars
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY . .

# Copy service account key for Firestore
COPY firestore-key.json /app/firestore-key.json
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/firestore-key.json

# Expose port
EXPOSE 8080

# Run the app
CMD ["python", "app.py"]
