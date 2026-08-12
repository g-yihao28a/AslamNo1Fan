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
EXPOSE 8008

# Start the application
CMD ["python", "api_gateway.py"]