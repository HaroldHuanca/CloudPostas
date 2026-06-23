FROM python:3.9-slim
WORKDIR /app
RUN pip install google-cloud-pubsub prometheus_client
COPY worker.py .
COPY gcp-credentials.json /app/credentials.json
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json
CMD ["python", "worker.py"]
