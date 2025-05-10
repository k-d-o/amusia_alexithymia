FROM balenalib/raspberrypi3-python:3.9-bullseye

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    libatlas-base-dev \
    libopenjp2-7 \
    libtiff5 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip3 install --no-cache-dir \
    RPi.GPIO \
    spidev \
    Pillow \
    numpy \
    opencv-python-headless

# Copy the display control script
COPY display_controller.py /usr/src/app/

# Set working directory
WORKDIR /usr/src/app

# Run the display controller
CMD ["python3", "display_controller.py"] 