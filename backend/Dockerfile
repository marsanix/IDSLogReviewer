FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (if any needed for mysql-connector)
# RUN apt-get update && apt-get install -y ...

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose the Flask port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
