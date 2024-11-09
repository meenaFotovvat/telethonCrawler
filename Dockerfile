# Use the official Python image
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the rest of the app code into the container
COPY . .

# Copy the session file and encryption key into the container (ensure these files exist locally)
COPY ./data/bookNook_session.session.enc /app/data/bookNook_session.session.enc
COPY ./data/encryption_key.key /app/data/encryption_key.key

# Expose port 8000 for Uvicorn
EXPOSE 8000

# Run the FastAPI app with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
