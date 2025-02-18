# Use an official lightweight Python base image
FROM python:3.10-slim

# Create a working directory in the container
WORKDIR /app

# Copy the requirements file first (for caching)
COPY requirements.txt /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
# (excluding .env if that exists locally)
COPY app.py /app

# Expose the Flask port (optional if you want clarity)
EXPOSE 5000

# Run the Flask server
CMD [ "python", "app.py" ]
