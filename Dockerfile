FROM python:3.10-slim

WORKDIR /app

# Copy & install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Cài đặt cron
RUN apt-get update && apt-get install -y cron && \
    chmod +x /app/cleanup.sh

# Copy cron file
COPY crontab /etc/cron.d/cleanup-cron

# Apply cron job
RUN chmod 0644 /etc/cron.d/cleanup-cron && \
    crontab /etc/cron.d/cleanup-cron

# Tạo log file cho cron
RUN touch /var/log/cron.log

# Expose Flask port
EXPOSE 5000

# Run cron + flask song song
CMD cron && flask run --host=0.0.0.0

