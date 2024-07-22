#!/usr/bin/ python

#################################################################################
#                                                                               #
# PowerMeter service controlling platform halt/wake-up button and status LED    #
#                                                                               #
# Halt signal is detected by sensing GPIO5                                      #
# Wake-up signal is detected by sensing  GPIO3, this however is only possible   #
# when pi is halted. GPIO3 signal changes during normal operation are ignored   #
# as long as GPIO26 is set to LOW                                               #
#                                                                               #
# LED status is indicated by UART TX (GPIO14). For this functionality to work   #
# UART controller has to be enabled in /boot/config.txt file by adding:         #
# enable_uart=1 in section [all].                                               #
#                                                                               #
#                                       may 2024, sp5gw, andrzej@mazur.info     #
#                                                                               #
#################################################################################


#
# sudo pip install is a must so package is available globally
# sudo pip install systemd-python --break-system-packages
#

import RPi.GPIO as GPIO
import time

from systemd import journal

import subprocess
import os

# Configure logging into systemd journal
# Use: journalctl -u listen-for-halt.service -n 20

def log_info(message):
	journal.send(message, PRIORITY=journal.LOG_INFO)

def log_error(message):
	journal.send(message, PRIORITY=journal.LOG_ERR)

print("Waiting for halt button to be pressed")
log_info("Waiting for halt button to be pressed")

haltButtonGpioPinNumber = 5
haltButtonRequiredPressDuration = 3

disableWakeUpPinNumber = 26

displayBacklightPinNumber = 22

GPIO.setmode(GPIO.BCM)
GPIO.setup(haltButtonGpioPinNumber,GPIO.IN)

GPIO.setup(disableWakeUpPinNumber,GPIO.OUT)
GPIO.output(disableWakeUpPinNumber, GPIO.LOW)

# ACT_LED is set to track cpu in config.txt
# modify this by setting it to always on
# this is to avoid led flashing when 
# measurement loop is running.

# Command and arguments for echo
actLedCmd = 'echo default-on | sudo tee /sys/class/leds/ACT/trigger'
os.system(actLedCmd)

try:
	while True:
		# Wait for the button to be pressed
		if GPIO.input(haltButtonGpioPinNumber) == GPIO.LOW: # Button pressed (assuming active-low)
			press_start_time = time.time()

			# Wait for the button to be released or held for 3 seconds
			while GPIO.input(haltButtonGpioPinNumber) == GPIO.LOW:
				time.sleep(0.1)
				press_duration = time.time() - press_start_time
				if press_duration >= haltButtonRequiredPressDuration:
					print("Halt button has been pressed")
					log_info("Halt button has been pressed")
					# Modify ACT_LED behaviour so it tracks cpu
					actLedCmd = 'echo cpu0 | sudo tee /sys/class/leds/ACT/trigger'
					os.system(actLedCmd)
                                        # Put Pi into sleep i.e. halt it
					subprocess.call(['sudo', 'shutdown', '-h', 'now'], shell=False)
					break
		time.sleep(0.1) # Adding small delay to avoid excessive GPU usage

except KeyboardInterupt:
	# Clean up GPIO settings before exiting
	GPIO.cleanup()
