FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "if [ \"${RUN_DB_INIT:-false}\" = \"true\" ]; then python init_db.py; fi; exec uvicorn main:app --host 0.0.0.0 --port \"${PORT:-8080}\""]
