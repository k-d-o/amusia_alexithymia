# Base image (balena base images are recommended)
FROM balenalib/raspberrypi3-python:3.10

# Set working directory
WORKDIR /usr/src/app

# Copy files
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Optional environment variables
ENV DB_HOST=localhost
ENV MQTT_PORT=1883

# What gets executed when the block starts
CMD ["python", "main.py"]
