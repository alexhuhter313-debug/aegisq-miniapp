FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Clone and install shadow313 as real engine
RUN git clone https://github.com/alexhuhter313-debug/shadow313.git /shadow313 \
    && pip install -e /shadow313[ai,web,reports,graph]

COPY . .

EXPOSE 8001

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8001"]
