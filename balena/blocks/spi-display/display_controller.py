#!/usr/bin/env python3

import os
import time
import spidev
import numpy as np
import cv2
import RPi.GPIO as GPIO
import requests
import logging
import atexit

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Disable GPIO warnings
GPIO.setwarnings(False)


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

        # Register cleanup function
        atexit.register(self.cleanup)

        # Initialize SPI
        self.spi = spidev.SpiDev()
        self.spi.open(self.spi_bus, self.spi_device)
        self.spi.max_speed_hz = 40000000
        self.spi.mode = 0b00
        self.spi.lsbfirst = False  # MSB first
        self.spi.bits_per_word = 8

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
            self.write_data(0x00)  # RGB order
        elif orientation == 1:  # Landscape
            self.write_data(0x60)  # RGB order
        elif orientation == 2:  # Portrait flipped
            self.write_data(0xC0)  # RGB order
        elif orientation == 3:  # Landscape flipped
            self.write_data(0xA0)  # RGB order

    def initialize_display(self):
        """Initialize the display with basic settings"""
        try:
            self.reset()
            
            self.write_cmd(self.ST7789_SWRESET)  # Software reset
            time.sleep(0.15)
            
            self.write_cmd(self.ST7789_SLPOUT)   # Sleep out
            time.sleep(0.15)
            
            # Set pixel format to RGB565
            self.write_cmd(self.ST7789_COLMOD)
            self.write_data(0x55)  # 16-bit color
            
            # Set porch control (from driver)
            self.write_cmd(0xB2)  # PORCTRL
            self.write_data(0x0C)
            self.write_data(0x0C)
            self.write_data(0x00)
            self.write_data(0x33)
            self.write_data(0x33)
            
            # Set gate control (from driver)
            self.write_cmd(0xB7)  # GCTRL
            self.write_data(0x35)
            
            # Set VDV and VRH enable
            self.write_cmd(0xC2)  # VDVVRHEN
            self.write_data(0x01)
            self.write_data(0xFF)
            
            # Set VRH
            self.write_cmd(0xC3)  # VRHS
            self.write_data(0x1B)
            
            # Set VDV
            self.write_cmd(0xC4)  # VDVS
            self.write_data(0x20)
            
            # Set VCOM
            self.write_cmd(0xBB)  # VCOMS
            self.write_data(0x1C)
            
            # Set VCOM offset
            self.write_cmd(0xC5)  # VCMOFSET
            self.write_data(0x20)
            
            # Set power control
            self.write_cmd(0xD0)  # PWCTRL1
            self.write_data(0xA4)
            self.write_data(0xA1)
            
            # Set positive gamma correction
            self.write_cmd(0xE0)  # PVGAMCTRL
            self.write_data(0x00)
            self.write_data(0x0C)
            self.write_data(0x11)
            self.write_data(0x0D)
            self.write_data(0x0C)
            self.write_data(0x07)
            self.write_data(0x2D)
            self.write_data(0x44)
            self.write_data(0x45)
            self.write_data(0x0F)
            self.write_data(0x17)
            self.write_data(0x16)
            self.write_data(0x2B)
            self.write_data(0x33)
            
            # Set negative gamma correction
            self.write_cmd(0xE1)  # NVGAMCTRL
            self.write_data(0x00)
            self.write_data(0x0C)
            self.write_data(0x11)
            self.write_data(0x0D)
            self.write_data(0x0C)
            self.write_data(0x07)
            self.write_data(0x2D)
            self.write_data(0x43)
            self.write_data(0x45)
            self.write_data(0x0F)
            self.write_data(0x16)
            self.write_data(0x16)
            self.write_data(0x2B)
            self.write_data(0x33)
            
            # Set orientation (default to landscape)
            self.set_orientation(3)
            
            # Enable inversion (from driver)
            self.write_cmd(self.ST7789_INVON)
            
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
            # Convert from BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Convert to RGB565 format using numpy
            r = frame_rgb[:, :, 0] & 0xF8  # Red
            g = frame_rgb[:, :, 1] & 0xFC  # Green
            b = frame_rgb[:, :, 2] >> 3    # Blue
            
            # Combine into RGB565 format
            rgb565 = ((r.astype(np.uint16) << 8) | 
                     (g.astype(np.uint16) << 3) | 
                     b.astype(np.uint16))
            
            # Convert to big-endian for ST7789
            rgb565 = rgb565.byteswap()
            
            # Convert to bytes
            buffer = rgb565.tobytes()

            # Display the image
            self.set_window(0, 0, self.width-1, self.height-1)
            GPIO.output(self.DC_PIN, GPIO.HIGH)

            # Send data in smaller chunks to avoid buffer overflow
            chunk_size = 4096  # Reduced chunk size to stay within SPI limits
            for i in range(0, len(buffer), chunk_size):
                chunk = buffer[i:i+chunk_size]
                if chunk:  # Only send if we have data
                    self.spi.writebytes(list(chunk))  # Convert bytes to list for writebytes

        except Exception as e:
            logger.error(f"Failed to display frame: {e}")
            # Don't re-raise the exception to allow playback to continue

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

            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_delay = 1.0 / fps if fps > 0 else 1.0 / \
                30.0  # Default to 30fps if can't get FPS

            logger.info(f"Playing video: {video_url}")
            logger.info(
                f"Original Resolution: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
            logger.info(f"FPS: {fps}")

            while True:
                ret, frame = cap.read()
                if not ret:
                    # Rewind to beginning
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue

                # Resize frame to match display resolution
                frame = cv2.resize(frame, (self.width, self.height))
                self.display_frame(frame)

                # Use a more precise sleep
                time.sleep(frame_delay)

        except Exception as e:
            logger.error(f"Error playing video: {e}")
        finally:
            if 'cap' in locals():
                cap.release()

    def cleanup(self):
        """Clean up GPIO and SPI resources"""
        try:
            GPIO.cleanup()
            if hasattr(self, 'spi'):
                self.spi.close()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


def main():
    try:
        display = ST7789Display()
        server_url = os.getenv('VIDEO_SERVER_URL')
        logger.info(
            f"Environment variable VIDEO_SERVER_URL value: {server_url}")

        if not server_url:
            logger.error("VIDEO_SERVER_URL environment variable is not set!")
            server_url = 'http://192.168.1.176:8080/video/test_1.mp4'
            logger.info(f"Using default URL: {server_url}")

        # Extract base URL without the video_1.html part
        base_url = server_url.rsplit('/', 1)[0]

        while True:
            try:
                # Try to play the video directly from the URL
                logger.info(f"Playing video from: {server_url}")
                display.play_video(server_url)

                # If we get here, the video finished or had an error
                logger.info("Video playback finished, waiting before retry...")
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