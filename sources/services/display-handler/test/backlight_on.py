import digitalio
import board

backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = False
