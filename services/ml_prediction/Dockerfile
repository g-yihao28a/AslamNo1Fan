# Base Image
FROM python:3.12-slim

# Set working directory inside the container
WORKDIR /app


# Copy requirements 
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose port 
EXPOSE 8011

# Start the application
CMD ["streamlit", "run", "prediction.py", "--server.port=8011", "--server.address=0.0.0.0"]