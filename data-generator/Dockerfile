FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir psycopg2-binary
COPY generator.py /app/
CMD ["python", "generator.py"]
