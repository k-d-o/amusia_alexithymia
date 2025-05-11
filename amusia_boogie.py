import RPi.GPIO as GPIO
import spidev
import time
import cv2
import numpy as np

# Configuration for ST7789 display
RST_PIN = 27
DC_PIN = 25
BL_PIN = 24  # Backlight pin, may not be needed for all displays

# Display dimensions - adjust based on your display
WIDTH = 320
HEIGHT = 240

# Initialize GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(RST_PIN, GPIO.OUT)
GPIO.setup(DC_PIN, GPIO.OUT)
if BL_PIN is not None:
    GPIO.setup(BL_PIN, GPIO.OUT)
    GPIO.output(BL_PIN, GPIO.HIGH)  # Turn backlight on

# Initialize SPI
spi = spidev.SpiDev()
spi.open(0, 0)  # Bus 0, Device 0
spi.max_speed_hz = 40000000
spi.mode = 0b00

# ST7789 Commands
ST7789_NOP = 0x00
ST7789_SWRESET = 0x01
ST7789_RDDID = 0x04
ST7789_RDDST = 0x09
ST7789_SLPIN = 0x10
ST7789_SLPOUT = 0x11
ST7789_PTLON = 0x12
ST7789_NORON = 0x13
ST7789_INVOFF = 0x20
ST7789_INVON = 0x21
ST7789_DISPOFF = 0x28
ST7789_DISPON = 0x29
ST7789_CASET = 0x2A
ST7789_RASET = 0x2B
ST7789_RAMWR = 0x2C
ST7789_RAMRD = 0x2E
ST7789_PTLAR = 0x30
ST7789_COLMOD = 0x3A
ST7789_MADCTL = 0x36

# Functions


def write_cmd(cmd):
    GPIO.output(DC_PIN, GPIO.LOW)
    spi.writebytes([cmd])


def write_data(data):
    GPIO.output(DC_PIN, GPIO.HIGH)
    spi.writebytes([data])


def reset():
    GPIO.output(RST_PIN, GPIO.HIGH)
    time.sleep(0.01)
    GPIO.output(RST_PIN, GPIO.LOW)
    time.sleep(0.01)
    GPIO.output(RST_PIN, GPIO.HIGH)
    time.sleep(0.01)


def set_orientation(orientation):
    """
    Set display orientation:
    0: 0 degrees (portrait)
    1: 90 degrees (landscape)
    2: 180 degrees (portrait flipped)
    3: 270 degrees (landscape flipped)
    """
    write_cmd(ST7789_MADCTL)  # Memory Data Access Control

    if orientation == 0:  # Portrait
        write_data(0x00)  # Top to Bottom, Left to Right, Normal mode
    elif orientation == 1:  # Landscape
        write_data(0x60)  # Left to Right, Bottom to Top, X/Y Exchange
    elif orientation == 2:  # Portrait flipped
        write_data(0xC0)  # Bottom to Top, Right to Left, X/Y Reflection
    elif orientation == 3:  # Landscape flipped
        # Right to Left, Top to Bottom, X/Y Exchange + Reflection
        write_data(0xA0)


def init():
    reset()

    write_cmd(ST7789_SWRESET)  # Software reset
    time.sleep(0.15)

    write_cmd(ST7789_SLPOUT)   # Sleep out
    time.sleep(0.15)

    write_cmd(ST7789_COLMOD)   # Set color mode
    write_data(0x55)           # 16-bit RGB color

    # Set orientation (default to landscape)
    set_orientation(3)

    write_cmd(ST7789_INVON)    # Inversion ON (use INVOFF for normal colors)

    write_cmd(ST7789_NORON)    # Normal display on
    time.sleep(0.05)

    write_cmd(ST7789_DISPON)   # Display on
    time.sleep(0.15)

    print("Display initialized")


def set_window(x_start, y_start, x_end, y_end):
    # Set X coordinates
    write_cmd(ST7789_CASET)
    write_data(x_start >> 8)
    write_data(x_start & 0xFF)
    write_data(x_end >> 8)
    write_data(x_end & 0xFF)

    # Set Y coordinates
    write_cmd(ST7789_RASET)
    write_data(y_start >> 8)
    write_data(y_start & 0xFF)
    write_data(y_end >> 8)
    write_data(y_end & 0xFF)

    # Ready to write to display RAM
    write_cmd(ST7789_RAMWR)


def clear_display(color=0):
    """Clear the display with a specified color (16-bit RGB565)"""
    set_window(0, 0, WIDTH-1, HEIGHT-1)

    # Split the color into high and low bytes
    high_byte = (color >> 8) & 0xFF
    low_byte = color & 0xFF

    # For better performance, send data in chunks
    GPIO.output(DC_PIN, GPIO.HIGH)

    buffer_size = 1024
    color_bytes = [high_byte, low_byte] * (buffer_size // 2)

    total_pixels = WIDTH * HEIGHT
    chunks = total_pixels // (buffer_size // 2)

    for _ in range(chunks):
        spi.writebytes(color_bytes)

    # Send remaining pixels
    remaining = total_pixels % (buffer_size // 2)
    if remaining > 0:
        spi.writebytes([high_byte, low_byte] * remaining)


def display_frame(frame):
    """Display a video frame on the screen"""
    # Resize frame to fit display
    frame = cv2.resize(frame, (WIDTH, HEIGHT))

    # Convert from BGR to RGB
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Convert to RGB565 format
    pixels = frame_rgb.reshape(-1, 3)  # Reshape to a list of pixels
    buffer = []

    for pixel in pixels:
        r, g, b = pixel
        rgb = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
        buffer.append((rgb >> 8) & 0xFF)  # High byte
        buffer.append(rgb & 0xFF)         # Low byte

    # Display the image
    set_window(0, 0, WIDTH-1, HEIGHT-1)
    GPIO.output(DC_PIN, GPIO.HIGH)

    # Send data in chunks to improve performance
    chunk_size = 4096
    buffer_bytes = bytes(buffer)  # Convert to bytes for faster transmission

    for i in range(0, len(buffer), chunk_size):
        chunk = buffer[i:i+chunk_size]
        spi.writebytes(chunk)


def stream_video(video_path=0):
    """
    Stream video to the display
    video_path: path to video file or camera index (0 for default camera)
    """
    # Open video file or camera
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print("Error: Could not open video source")
        return

    print(
        f"Video opened successfully: {'Camera' if video_path == 0 else video_path}")
    print(
        f"Resolution: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
    print(f"FPS: {cap.get(cv2.CAP_PROP_FPS)}")

    try:
        while True:
            # Read a frame
            ret, frame = cap.read()

            if not ret:
                print("End of video or frame could not be read")
                # If it's a video file, rewind to beginning
                if video_path != 0:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                else:
                    break

            # Display frame on ST7789
            display_frame(frame)

            # Check for quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        # Release video capture
        cap.release()
        cv2.destroyAllWindows()


# Main program
try:
    print("Initializing display...")
    init()

    print("Setting orientation to landscape...")
    set_orientation(1)  # 1 = landscape mode (90 degrees)

    print("Clearing display...")
    clear_display(0x0000)  # Black

    # Stream video (provide a file path or 0 for camera)
    video_source = 0  # Change to a file path like "video.mp4" to use a video file
    print(
        f"Streaming video from: {'Camera' if video_source == 0 else video_source}")
    stream_video(video_source)

except KeyboardInterrupt:
    print("Exiting...")
finally:
    GPIO.cleanup()
    spi.close()
