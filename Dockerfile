# Use the official Python image from the Docker Hub
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the required packages
RUN pip install --no-cache-dir -r requirements.txt

# Install ImageMagick
RUN apt-get update && apt-get install -y \
    imagemagick \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy the rest of the application code into the container
COPY . .

# Command to run the application
CMD ["python", "main.py"]
