# Use the official Python slim image from the Docker Hub
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the required packages
RUN pip install --no-cache-dir -r requirements.txt

# Install ImageMagick and ffmpeg
RUN apt-get update && apt-get install -y \
    imagemagick \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Expose the port that Flask is running on
EXPOSE 5000

# Copy the rest of the application code and the bash script
COPY . .

# Make the bash script executable
CMD gunicorn app:app & python3 main.py
