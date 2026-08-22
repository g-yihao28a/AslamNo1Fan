FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY load_data.py .

# Copy the Excel files into the /k8s_data directory inside the container
COPY data_files/*.xlsx /data/

CMD ["python", "load_data.py"]