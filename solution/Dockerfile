FROM python:3.12-alpine3.21


RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    python3-dev \
    curl
RUN apk add --no-cache build-base


WORKDIR /usr/src/app

COPY  requirements_chill.txt .
RUN pip install --no-cache-dir -r  requirements_chill.txt

COPY . .

ENV SERVER_PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "uvicorn main:app --host REDACTED --port ${SERVER_PORT}"]
