# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT
# -*- coding: utf-8 -*-

#################################################################################
#                                                                               #
# PowerMeter service handling TFT display and band selector buttons.            #
#                                                                               #
# Band selector buttons status is continously checked and currently selected    #
# band is calculated. Band selection is saved in file ./bandselector.value      #
# and later used by measurement loop service.                                   #
# Latest measured power value in dBm and Watts is continously fetched from      #
# file: ../measurement-loop/powermeas.value.                                    #
#                                                                               #
# In current version this program is not instrumented with journal logging      #
#                                                                               #
#                                       may 2024, sp5gw, andrzej@mazur.info     #
#                                                                               #
#################################################################################


#
# sudo pip install is a must so package is available globally
# sudo pip install systemd-python --break-system-packages
#


import sys
import time
import subprocess
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789

def clearDisplay():
	# Create blank image for drawing.
	# Make sure to create image with mode 'RGB' for full color.
	width = disp.width
	height = disp.height
	image = Image.new("RGB", (width, height))
	rotation = 0
	# Draw a black filled box to clear the image.
	draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))
	disp.image(image, rotation)

def displayBacklight(status):
        # Turn on the backlight when status = False
        # Turn off the backlight when status = True
        # This is inverted logic compared to original Adafruit design!
        # Inversion of GPIO22 is done in HW by NAND gate 
        backlight = digitalio.DigitalInOut(board.D22)
        backlight.switch_to_output()
        backlight.value = status

# Configure Up and Down buttons (band selector)
buttonUp = digitalio.DigitalInOut(board.D23)
buttonDown = digitalio.DigitalInOut(board.D24)
buttonUp.switch_to_input()
buttonDown.switch_to_input()

# Configuration for CS and DC pins (these are FeatherWing defaults on M0/M4):
cs_pin = digitalio.DigitalInOut(board.CE0)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = None
# Config for display baudrate (default max is 24mhz):
BAUDRATE = 64000000
# Setup SPI bus using hardware SPI:
spi = board.SPI()
# Create the ST7789 display:
disp = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
    width=240,
    height=240,
    x_offset=0,
    y_offset=80,
)

# Create blank image for drawing.
# Make sure to create image with mode 'RGB' for full color.
width = disp.width
height = disp.height
image = Image.new("RGB", (width, height))
rotation = 0
# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)
# Draw a black filled box to clear the image.
draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))
disp.image(image, rotation)

# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height - padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0
# Alternatively load a TTF font.  Make sure the .ttf font file is in the
# same directory as the python script!
# Some other nice fonts to try: http://www.dafont.com/bitmap.php
fontRegular = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
fontLarge = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",80)

# Turn on the backlight
# GPIO22 controling Backlight is inverted by NAND gate!
displayBacklight(False)


# Define the file name with power values to display
fileName = '../measurement-loop/powermeas.value'

# Initialize variables to store the power values
powerdBm = "Err"
powerWatt = "Err"

# Initialize band selector
bandSelectorIdx = 1 # Default band 80 m
bandSelector = [" 160", "  80", "  60", "  40", "  30", " 20", "  17", "  15", "  12", "  10", "   6"]

try:
        while True:

                if buttonUp.value == True:
                        if bandSelectorIdx == 10:
                                bandSelectorIdx = 0
                        else:
                                bandSelectorIdx += 1
                if buttonDown.value == True:
                        if bandSelectorIdx == 0:
                                bandSelectorIdx = 10
                        else:
                                bandSelectorIdx -= 1
                #Store band in the file
                with open("./bandselector.value", "w") as file:
                        # Write a line of text to the file
                        file.write("bandSelectorIdx:" + str(bandSelectorIdx) + "\n")
                        file.write("bandSelector:" + str(bandSelector[bandSelectorIdx]) + "m" + "\n")

                # Draw a black filled box to clear the image.
                draw.rectangle((0, 0, width, height), outline=0, fill=0)

                # Power readout preparation
                textEmptyLine = "ABC"

                # Open and read the file
                with open(fileName, 'r') as file:
                        # Read all lines from the file
                        lines = file.readlines()
                        # Iterate over each line
                        for line in lines:
    			        # Split the line by the colon to separate key and value
                                key, value = line.strip().split(':')
                                # Store the values in the respective variables
                                if key == 'Pwr_dBm':
                                        powerdBm = value
                                elif key == 'Pwr_Watt':
                                        powerWatt = value

                #powerWatt = str(int(powerWatt) + 30) # test to exceed 100W reading

                textBanner = "Power:"
                textPowerdBm = "            " + str(powerdBm) + "dBm"

                if int(powerWatt) > 99:
                        textPowerWatt = " " + str(powerWatt)
                else:
                        textPowerWatt = "   " + str(powerWatt)

                textPowerWattUnit = "W"

                textBandSelector = "            band:" + bandSelector[bandSelectorIdx] + "m"

                # Write prepared lines of text.
                y = top

                draw.text((x,y), textEmptyLine, font=fontRegular, fill="#000000")
                bbox = draw.textbbox((x, y), textEmptyLine, font=fontRegular)
                y += (2*(bbox[3] - bbox[1]))

                draw.text((x,y), textBanner, font=fontRegular, fill="#FFFFFF")
                bbox = draw.textbbox((x, y), textBanner, font=fontRegular)
                y += (bbox[3] - bbox[1])

                draw.text((x,y), textEmptyLine, font=fontRegular, fill="#000000")
                bbox = draw.textbbox((x, y), textEmptyLine, font=fontRegular)
                y += (bbox[3] - bbox[1])

                draw.text((x, y), textPowerWatt , font=fontLarge, fill="#FF00FF")
                bbox = draw.textbbox((x,y), textPowerWatt, font=fontLarge)

                x += (bbox[2] - bbox[0])
                y += (bbox[3] - bbox[1])
                y = y - 10

                draw.text((x,y), textPowerWattUnit, font=fontRegular, fill="#FF00FF")
                bbox = draw.textbbox((x,y),textPowerWattUnit, font=fontRegular)

                x = 0

                draw.text((x,y), textEmptyLine, font=fontRegular, fill="#000000")
                bbox = draw.textbbox((x, y), textEmptyLine, font=fontRegular)
                y += (2*(bbox[3] - bbox[1]))

                draw.text((x, y), textPowerdBm, font=fontRegular, fill="#FFFF00")
                bbox = draw.textbbox((x,y), textPowerdBm, font=fontRegular)
                y += (bbox[3] - bbox[1])

                draw.text((x, y), textEmptyLine, font=fontRegular, fill="#000000")
                bbox = draw.textbbox((x,y), textEmptyLine, font=fontRegular)
                y += (bbox[3] - bbox[1])

                draw.text((x, y), textBandSelector, font=fontRegular, fill="#FFFFFF")

                # Display image.
                disp.image(image, rotation)
                time.sleep(0.1)
except KeyboardInterrupt:
	clearDisplay()
	displayBacklight(False)
