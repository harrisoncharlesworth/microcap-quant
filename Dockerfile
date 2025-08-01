FROM python:3.11-slim

# Set timezone to Eastern Time
ENV TZ=America/New_York
RUN apt-get update && apt-get install -y \
    tzdata \
    gcc \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Install the package in development mode
RUN pip install -e .

# Create directories for logs and state
RUN mkdir -p logs data

# Add health check - check for any recent log activity or heartbeat
HEALTHCHECK --interval=2m --timeout=30s --start-period=30s --retries=5 \
    CMD tail -100 auto_trader.log | grep -E "(Scheduler heartbeat|Starting|Complete|INFO)" | tail -1 | grep -q $(date +%Y-%m-%d) || exit 1

# Run the bot
CMD ["python", "-m", "auto_trader.automated_trader"]
