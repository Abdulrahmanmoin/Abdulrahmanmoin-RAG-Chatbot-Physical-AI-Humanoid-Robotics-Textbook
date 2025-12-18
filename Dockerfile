# Use an official Python runtime as the base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies needed for Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file first to leverage Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the backend source code
COPY . .

# Expose the port that the app runs on
EXPOSE 7860

# Set environment variables for Hugging Face Spaces
ENV HOST=0.0.0.0
ENV PORT=7860

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash --uid 1000 user
# Change ownership of the app directory to the non-root user
RUN chown -R user:user /app
USER 1000

# Command to run the application using uvicorn explicitly
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "7860"]
