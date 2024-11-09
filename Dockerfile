# Use the official Python image as the base image
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt to the container and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code (including your FastAPI app and .env file) into the container
COPY . /app/

# Create the necessary data directory in the container (for persistent storage)
RUN mkdir -p /app/data

# Expose port 8000 for Uvicorn to run FastAPI
EXPOSE 8000

# Set environment variables for FastAPI (ensure it loads the .env file)
ENV PYTHONUNBUFFERED=1

# Run the FastAPI app with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
