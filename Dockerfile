FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir google-cloud-firestore google-cloud-bigquery google-cloud-aiplatform requests pyyaml markdown matplotlib pandas
CMD ["python", "main.py"]
