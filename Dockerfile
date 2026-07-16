# Works on Raspberry Pi (arm64/armv7) and x86 alike
FROM python:3.11-slim

WORKDIR /app

# vcgencmd (used for CPU temp) lives on the host, not in the container —
# app.py already falls back to /sys/class/thermal if it's missing, so no
# extra package needed here for that.

COPY requirements.txt .
# psutil and lgpio have no prebuilt wheels for 32-bit ARM, so they compile
# from source — install gcc for the build, then remove it to keep the image slim
RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y --auto-remove gcc libc6-dev \
    && rm -rf /var/lib/apt/lists/*

COPY . .

EXPOSE 5000

CMD ["python3", "app.py"]
