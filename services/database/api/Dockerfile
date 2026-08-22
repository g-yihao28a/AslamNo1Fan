FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY database_services.py .

EXPOSE 8012

CMD ["python", "database_services.py"]