FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir paho-mqtt requests python-dotenv
COPY src/ .

CMD ["python", "-u", "dynatrace-metrics-ingest.py"]