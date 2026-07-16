# Works on Raspberry Pi (arm64/armv7) and x86 alike
FROM python:3.11-slim

WORKDIR /app

# vcgencmd (used for CPU temp) lives on the host, not in the container —
# app.py already falls back to /sys/class/thermal if it's missing, so no
# extra package needed here for that.

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python3", "app.py"]
