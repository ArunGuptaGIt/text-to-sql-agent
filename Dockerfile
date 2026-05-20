FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create logs directory
RUN mkdir -p logs

EXPOSE 8000 8501

# No default CMD, defined in docker-compose.yml
