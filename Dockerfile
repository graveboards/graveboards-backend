FROM python:3.12

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY entrypoint.sh /app/
COPY wait-for-it.sh /app/

RUN chmod +x /app/entrypoint.sh /app/wait-for-it.sh

ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["uvicorn", "main:connexion_app", "--host", "0.0.0.0", "--port", "8000"]
