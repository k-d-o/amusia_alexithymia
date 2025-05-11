FROM balenalib/raspberrypi3-debian:bullseye

# Install Python and system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    libatlas-base-dev \
    libopenjp2-7 \
    libtiff5 \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libxcb1-dev \
    libopenblas0 \
    libavcodec58 \
    libavformat58 \
    libavutil56 \
    libswscale-dev \
    libswresample-dev \
    && rm -rf /var/lib/apt/lists/*


# Use piwheels for prebuilt ARM wheels
RUN pip3 install --no-cache-dir --extra-index-url https://www.piwheels.org/simple \
    RPi.GPIO \
    spidev \
    Pillow \
    numpy \
    requests \
    opencv-python-headless

# Copy the display control script
COPY display_controller.py /usr/src/app/

# Set working directory
WORKDIR /usr/src/app

# Run the display controller
CMD ["python3", "display_controller.py"] 