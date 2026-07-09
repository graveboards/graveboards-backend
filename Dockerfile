FROM python:3.14-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/usr/local --root-user-action=ignore -r requirements.txt

FROM python:3.14-slim AS test-builder

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /build

COPY requirements.txt .
COPY requirements-dev.txt .
RUN pip install --no-cache-dir --prefix=/usr/local --root-user-action=ignore -r requirements.txt -r requirements-dev.txt

FROM python:3.14-slim AS runner

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

COPY --from=builder /usr/local /usr/local

COPY . .

COPY entrypoint.sh /app
COPY wait-for-it.sh /app

RUN sed -i 's/\r$//' /app/entrypoint.sh /app/wait-for-it.sh && \
    chmod +x /app/entrypoint.sh /app/wait-for-it.sh

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]

CMD [ \
    "uvicorn", \
    "app.connexion_app:create_connexion_app", \
    "--factory", \
    "--host", "0.0.0.0", \
    "--port", "8000" \
]

FROM python:3.14-slim AS test-runner

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

COPY --from=test-builder /usr/local /usr/local

COPY --chmod=755 . .

RUN sed -i 's/\r$//' /app/entrypoint.sh /app/wait-for-it.sh

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]

CMD [ "pytest", "-v" ]
