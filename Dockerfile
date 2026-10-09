FROM python:3.11-slim AS backend

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# For production: serve frontend via nginx + backend via uvicorn
FROM nginx:alpine AS frontend
COPY frontend/index.html /usr/share/nginx/html/index.html
COPY --from=backend /app /app

# Install python in nginx container
RUN apk add --no-cache python3 py3-pip && \
    pip3 install --break-system-packages -r /app/requirements.txt

EXPOSE 80 8001

# Start both nginx and backend
CMD sh -c "nginx && uvicorn backend.main:app --host 0.0.0.0 --port 8001"
