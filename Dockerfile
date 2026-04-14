FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY pyproject.toml README.md ./
COPY liquidsniper ./liquidsniper
COPY IntradayTrading/engine ./IntradayTrading/engine
COPY IntradayTrading/spec ./IntradayTrading/spec

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

CMD ["python", "-V"]
