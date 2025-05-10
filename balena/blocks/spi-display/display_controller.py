#!/usr/bin/env python3

import os
import time
import spidev
import numpy as np
import cv2
import RPi.GPIO as GPIO
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ST7789Display:
    def __init__(self):
        # Get configuration from environment variables
        self.width = int(os.getenv('DISPLAY_WIDTH', 320))
        self.height = int(os.getenv('DISPLAY_HEIGHT', 240))
        self.spi_bus = int(os.getenv('SPI_BUS', 0))
        self.spi_device = int(os.getenv('SPI_DEVICE', 0))
        
        # GPIO pins
        self.RST_PIN = int(os.getenv('RST_PIN', 27))
        self.DC_PIN = int(os.getenv('DC_PIN', 25))
        self.BL_PIN = int(os.getenv('BL_PIN', 24))
        
        # Initialize GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.RST_PIN, GPIO.OUT)
        GPIO.setup(self.DC_PIN, GPIO.OUT)
        if self.BL_PIN is not None:
            GPIO.setup(self.BL_PIN, GPIO.OUT)
            GPIO.output(self.BL_PIN, GPIO.HIGH)  # Turn backlight on
        
        # Initialize SPI
        self.spi = spidev.SpiDev()
        self.spi.open(self.spi_bus, self.spi_device)
        self.spi.max_speed_hz = 40000000
        self.spi.mode = 0b00
        
        # ST7789 Commands
        self.ST7789_NOP = 0x00
        self.ST7789_SWRESET = 0x01
        self.ST7789_RDDID = 0x04
        self.ST7789_RDDST = 0x09
        self.ST7789_SLPIN = 0x10
        self.ST7789_SLPOUT = 0x11
        self.ST7789_PTLON = 0x12
        self.ST7789_NORON = 0x13
        self.ST7789_INVOFF = 0x20
        self.ST7789_INVON = 0x21
        self.ST7789_DISPOFF = 0x28
        self.ST7789_DISPON = 0x29
        self.ST7789_CASET = 0x2A
        self.ST7789_RASET = 0x2B
        self.ST7789_RAMWR = 0x2C
        self.ST7789_RAMRD = 0x2E
        self.ST7789_PTLAR = 0x30
        self.ST7789_COLMOD = 0x3A
        self.ST7789_MADCTL = 0x36
        
        self.initialize_display()

    def write_cmd(self, cmd):
        GPIO.output(self.DC_PIN, GPIO.LOW)
        self.spi.writebytes([cmd])

    def write_data(self, data):
        GPIO.output(self.DC_PIN, GPIO.HIGH)
        self.spi.writebytes([data])

    def reset(self):
        GPIO.output(self.RST_PIN, GPIO.HIGH)
        time.sleep(0.01)
        GPIO.output(self.RST_PIN, GPIO.LOW)
        time.sleep(0.01)
        GPIO.output(self.RST_PIN, GPIO.HIGH)
        time.sleep(0.01)

    def set_orientation(self, orientation):
        """Set display orientation:
        0: 0 degrees (portrait)
        1: 90 degrees (landscape)
        2: 180 degrees (portrait flipped)
        3: 270 degrees (landscape flipped)
        """
        self.write_cmd(self.ST7789_MADCTL)
        if orientation == 0:  # Portrait
            self.write_data(0x00)
        elif orientation == 1:  # Landscape
            self.write_data(0x60)
        elif orientation == 2:  # Portrait flipped
            self.write_data(0xC0)
        elif orientation == 3:  # Landscape flipped
            self.write_data(0xA0)

    def initialize_display(self):
        """Initialize the display with basic settings"""
        try:
            self.reset()
            
            self.write_cmd(self.ST7789_SWRESET)  # Software reset
            time.sleep(0.15)
            
            self.write_cmd(self.ST7789_SLPOUT)   # Sleep out
            time.sleep(0.15)
            
            self.write_cmd(self.ST7789_COLMOD)   # Set color mode
            self.write_data(0x55)                # 16-bit RGB color
            
            # Set orientation (default to landscape)
            self.set_orientation(3)
            
            self.write_cmd(self.ST7789_INVON)    # Inversion ON
            
            self.write_cmd(self.ST7789_NORON)    # Normal display on
            time.sleep(0.05)
            
            self.write_cmd(self.ST7789_DISPON)   # Display on
            time.sleep(0.15)
            
            logger.info("Display initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize display: {e}")
            raise

    def set_window(self, x_start, y_start, x_end, y_end):
        # Set X coordinates
        self.write_cmd(self.ST7789_CASET)
        self.write_data(x_start >> 8)
        self.write_data(x_start & 0xFF)
        self.write_data(x_end >> 8)
        self.write_data(x_end & 0xFF)

        # Set Y coordinates
        self.write_cmd(self.ST7789_RASET)
        self.write_data(y_start >> 8)
        self.write_data(y_start & 0xFF)
        self.write_data(y_end >> 8)
        self.write_data(y_end & 0xFF)

        # Ready to write to display RAM
        self.write_cmd(self.ST7789_RAMWR)

    def display_frame(self, frame):
        """Display a video frame on the screen"""
        try:
            # Resize frame to fit display
            frame = cv2.resize(frame, (self.width, self.height))

            # Convert from BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Convert to RGB565 format
            pixels = frame_rgb.reshape(-1, 3)
            buffer = []

            for pixel in pixels:
                r, g, b = pixel
                rgb = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
                buffer.append((rgb >> 8) & 0xFF)  # High byte
                buffer.append(rgb & 0xFF)         # Low byte

            # Display the image
            self.set_window(0, 0, self.width-1, self.height-1)
            GPIO.output(self.DC_PIN, GPIO.HIGH)

            # Send data in chunks to improve performance
            chunk_size = 4096
            buffer_bytes = bytes(buffer)

            for i in range(0, len(buffer), chunk_size):
                chunk = buffer[i:i+chunk_size]
                self.spi.writebytes(chunk)

        except Exception as e:
            logger.error(f"Failed to display frame: {e}")

    def play_video(self, video_url):
        """Play a video from a URL"""
        try:
            response = requests.get(video_url, stream=True)
            if response.status_code != 200:
                logger.error(f"Failed to fetch video: {response.status_code}")
                return

            # Create a temporary file to store the video
            with open('/tmp/video.mp4', 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            # Open video file
            cap = cv2.VideoCapture('/tmp/video.mp4')
            if not cap.isOpened():
                logger.error("Could not open video file")
                return

            logger.info(f"Playing video: {video_url}")
            logger.info(f"Resolution: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
            logger.info(f"FPS: {cap.get(cv2.CAP_PROP_FPS)}")

            while True:
                ret, frame = cap.read()
                if not ret:
                    # Rewind to beginning
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue

                self.display_frame(frame)
                time.sleep(1/30)  # Control frame rate

        except Exception as e:
            logger.error(f"Error playing video: {e}")
        finally:
            if 'cap' in locals():
                cap.release()

def main():
    try:
        display = ST7789Display()
        server_url = os.getenv('VIDEO_SERVER_URL', 'http://localhost:8080')
        
        while True:
            try:
                # Get list of available videos
                response = requests.get(f"{server_url}/videos")
                if response.status_code == 200:
                    videos = response.json()
                    for video in videos:
                        video_url = f"{server_url}/video/{video}"
                        logger.info(f"Playing video: {video}")
                        display.play_video(video_url)
                else:
                    logger.error("Failed to fetch video list")
                    time.sleep(5)
            except requests.exceptions.RequestException as e:
                logger.error(f"Network error: {e}")
                time.sleep(5)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main() 