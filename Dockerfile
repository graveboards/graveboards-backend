FROM python:3.14

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY entrypoint.sh /app
COPY wait-for-it.sh /app

RUN sed -i 's/\r$//' /app/entrypoint.sh /app/wait-for-it.sh && \
    chmod +x /app/entrypoint.sh /app/wait-for-it.sh

ENTRYPOINT ["/app/entrypoint.sh"]

CMD [ \
    "uvicorn", \
    "app.connexion_app:create_connexion_app", \
    "--factory", \
    "--host", "0.0.0.0", \
    "--port", "8000", \
    "--log-config", "logging.uvicorn.yaml" \
]
