
#!/usr/bin/ python

####################################################################################
#                                                                                  #
# Periodic measurement of output voltage from AD8703 logarythmic amplifier,        #
# using Ina219 ADC. Measured voltage is converted to power in dBm using linear     #
# approximation.Formula calculating power value based on measured voltage is given #
# per band. Attenuation of measured power value by -40dB is assumed by the         #
# routine. Calculated power value in dBm is stored in file ./powermeas.value       #
# Information aboout current measurement band is fetched from                      #
# ../display-handler/bandselector.value file.                                      #
#                                                                                  #
#                                     may 2024, sp5gw, andrzej@mazur.info          #
#                                                                                  #
####################################################################################


#
# sudo pip install is a must for the package to be available globally
# sudo pip install systemd-python --break-system-packages
# sudo pip3 install adafruit-circuitpython-ina219 --break-system-packages
#

import time
import board
from adafruit_ina219 import ADCResolution, BusVoltageRange, INA219

from systemd import journal

# Configure logging into systemd journal
# Use: journal -u measurement_loop.service -n 20

def logInfo(message):
    journal.send(message, PRIORITY=journal.LOG_INFO)
    print(message)

def logErr(message):
    journal.send(message, PRIORITY=journal.LOG_ERR)
    print(message)


i2c_bus = board.I2C()

ina1 = INA219(i2c_bus,addr=0x40)

ina1.bus_adc_resolution = ADCResolution.ADCRES_12BIT_32S
ina1.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_32S
ina1.bus_voltage_range = BusVoltageRange.RANGE_16V

logInfo("Starting measurement loop...")

# Measurement loop
try:
    while True:
            bus_voltage1 = ina1.bus_voltage        # voltage on V- (load side)
            shunt_voltage1 = ina1.shunt_voltage    # voltage between V+ and V- across the shunt
            psu_voltage1 = bus_voltage1 + shunt_voltage1

            bandSelector = "Err"
            with open('../display-handler/bandselector.value', 'r') as file:
                linesInFile = file.readlines()
                if len(linesInFile) > 1:
                        secondLineInFile = linesInFile[1]
                        bandSelector = secondLineInFile.split(":", 1)[1].strip()
                        print(bandSelector)
                else:
                        logErr("bandselector.value  file has less than two lines.")
                        logErr("setting bandSelector to default 80m band")
                        bandSelector = "80m"

            if bandSelector == "160m":  #1800kHz
                power_dbm = ((psu_voltage1-1.153)/0.024)
            elif bandSelector == "80m": #3500kHz
                power_dbm = ((psu_voltage1 - 1.1797)/0.0234)
            elif bandSelector == "60m": #5000kHz
                power_dbm = ((psu_voltage1-1.1643)/0.0237)
            elif bandSelector == "40m": #7000kHz
                power_dbm = ((psu_voltage1-1.149)/0.024)
            elif bandSelector == "30m": #10000kHz
                power_dbm = ((psu_voltage1-1.149)/0.024)
            elif bandSelector == "20m": #14000kHz
                power_dbm = ((psu_voltage1-1.1603)/0.0237)
            elif bandSelector == "17m": #18000kHz
                power_dbm = ((psu_voltage1-1.129)/0.024)
            elif bandSelector == "15m": #21000kHz
                power_dbm = ((psu_voltage1-1.1296)/0.0243)
            elif bandSelector == "12m": #24500kHz
                power_dbm = ((psu_voltage1-1.1603)/0.0237)
            elif bandSelector == "10m": #28000kHz
                power_dbm = ((psu_voltage1-1.141)/0.024)
            elif bandSelector == "6m": #50000MHz
                power_dbm = ((psu_voltage1-1.1216)/0.0243)
            else:
                logErr("unsuported band selected, exiting the program...")
                exit (1)

            power_watt = 0.001*(10**(power_dbm/10))
    
            # INA219 measure bus voltage on the load side. So PSU voltage = bus_voltage + shunt_voltage
            print("PSU Voltage:{:6.3f}V".format(psu_voltage1))
            print("RMS RF Power: {:6.1f}dBm".format(power_dbm))
            print("RMS RF Power: {:6.0f}W".format(power_watt))
            print("")
            print("")
            # Write measurement values to the file in two separate lines
            with open('powermeas.value', 'w') as file:
                file.write("Pwr_dBm:" + str(round(power_dbm,1)) + "\n")
                file.write("Pwr_Watt:" + str(round(power_watt))+ "\n")
            # File is automatically closed here
            time.sleep(1)
except KeyboardInterrupt:
    logInfo("Program terminated by user")
