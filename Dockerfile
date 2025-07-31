FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the trading bot
COPY trade_bot.py .

# Create directories for logs and state
RUN mkdir -p logs

# Run the bot
CMD ["python", "trade_bot.py"]
