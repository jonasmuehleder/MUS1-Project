FROM python:3.11-alpine
WORKDIR /app
# Note: Some python packages require 'gcc' or 'musl-dev' to install on Alpine
RUN pip install --no-cache-dir paho-mqtt requests python-dotenv
COPY src/ .
CMD ["python", "-u", "dynatrace-metrics-ingest.py"]