# Use the official Python image from the Docker Hub
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code into the container
COPY . .

# Set environment variables (optional, can also be set in a .env file)
ENV DELAY=30
ENV JSON_DB_FILENAME=fire_alerts.json
ENV PUSHOVER_TOKEN=your_pushover_token
ENV PUSHOVER_USER=your_pushover_user

# Run the Python script
CMD ["python", "fire_notifier.py"]
