#
# Power supply interface for the DiDeBoCCS
# Controls the high voltage power supply in the Discharge Demo Box (DiDeBoCCS)
#

import Adafruit_BBIO.ADC as ADC
import Adafruit_BBIO.GPIO as GPIO
from time import sleep


PIN_analog = "P9_40" # P9_40 is AIN1
PIN_hv225V = "P8_7"
PIN_hv100V = "P8_9"
PIN_hv50V = "P8_11"
PIN_hv25V = "P8_15"
PIN_hv12V = "P8_17"

DRIVER_STRENGTH_UNKNOWN = 0
DRIVER_STRENGTH_CABLECHECK = 1
DRIVER_STRENGTH_PRECHARGE = 2
DRIVER_STRENGTH_CURRENTDEMAND = 3
DRIVER_STRENGTH_WELDINGDETECTION = 4

PIN_hv_connect_load = "P8_18" # Control the relay which connects the light bulbs to the HV

def boolToGpiostate(x):
    # Convert any non-zero value to GPIO.HIGH, and zero to GPIO.LOW.
    if (x!=0):
        return GPIO.HIGH
    else:
        return GPIO.LOW


class powersupplyInterface():
    def setVoltage(self, targetVoltage):
        if (self.selectedDriverStrength==DRIVER_STRENGTH_CURRENTDEMAND):
            # Special case for the discharge demo box: In currentdemand, we do NOT want
            # to use our small step-up converter to charge the car. That's why we set
            # the target voltage of the converter to zero. It will get physical voltage
            # from the car, and this is fine, because the step-up does not actively pull
            # the voltage down, it has output diodes integrated.
            targetVoltage = 0
            
        if (targetVoltage<=220):
            GPIO.output(PIN_hv225V, GPIO.LOW)
            if (targetVoltage>100+50+25+12):
                targetVoltage = 100+50+25+12
        else:
            # special case, because the most significant output has 225V instead of "binary-correct" 200V.
            # We get a gap between 175V and 230V, but this range is not of interest anyway.
            GPIO.output(PIN_hv225V, GPIO.HIGH)
            targetVoltage -= 225
            if (targetVoltage<0):
                targetVoltage = 0
            if (targetVoltage>100+50+25+12):
                targetVoltage = 100+50+25+12
        b = int(targetVoltage / 12)
        GPIO.output(PIN_hv100V, boolToGpiostate(b & 8))
        GPIO.output(PIN_hv50V, boolToGpiostate(b & 4))
        GPIO.output(PIN_hv25V, boolToGpiostate(b & 2))
        GPIO.output(PIN_hv12V, boolToGpiostate(b & 1))

    def readPhysicalVoltage(self):
        uHvFeedbackBBB_V = ADC.read(PIN_analog) * 1.8 # 1.8V is maximum value on beaglebone pin
        OFFSET_AT_ZERO_DC_V = 0.510 # The muehlpower voltage measurement board provides this voltage while U_HV=0
        GAIN = 386 # The combined scaling factor
        uHvMeasured_V = (uHvFeedbackBBB_V - OFFSET_AT_ZERO_DC_V) * GAIN
        return uHvMeasured_V
        
    def readPhysicalCurrent(self):
        return 10 # for demo, just tell the car that we are charging with 10A
        
    def isPhysicalVoltageMeasurementPossible(self):
        return True # The module supports physical voltage measurement.

    def selectDriverForCableCheck(self):
        # very weak driver strengh, e.g. for cable check
        #print("selecting weakest driver for cable check")
        self.selectedDriverStrength = DRIVER_STRENGTH_CABLECHECK
        # todo: Use digital output to select a high-impedance driver
        # turning the bulb load off, to avoid that the bulbs short the cable check voltage
        GPIO.output(PIN_hv_connect_load, GPIO.LOW)

    def selectDriverForPrecharge(self):
        #print("selecting driver for precharge")
        self.selectedDriverStrength = DRIVER_STRENGTH_PRECHARGE
        # todo: use digital output to select a mid-impedance driver
        # turning the bulb load off, to avoid that the bulbs short the precharge voltage
        GPIO.output(PIN_hv_connect_load, GPIO.LOW)

    def selectDriverForCurrentDemand(self):
        #print("selecting driver for current demand")
        self.selectedDriverStrength = DRIVER_STRENGTH_CURRENTDEMAND
        # todo: use digital output to select the powerful driver
        # turning the bulb load on
        GPIO.output(PIN_hv_connect_load, GPIO.HIGH)
        
    def selectDriverForWeldingDetection(self):
        #print("selecting driver for welding detection")
        self.selectedDriverStrength = DRIVER_STRENGTH_WELDINGDETECTION
        # turning the bulb load off
        GPIO.output(PIN_hv_connect_load, GPIO.LOW)
        

    def __init__(self):
        ADC.setup()
        GPIO.setup(PIN_hv225V, GPIO.OUT)
        GPIO.setup(PIN_hv100V, GPIO.OUT)
        GPIO.setup(PIN_hv50V, GPIO.OUT)
        GPIO.setup(PIN_hv25V, GPIO.OUT)
        GPIO.setup(PIN_hv12V, GPIO.OUT)
        GPIO.setup(PIN_hv_connect_load, GPIO.OUT)

        GPIO.output(PIN_hv225V, GPIO.LOW)
        GPIO.output(PIN_hv100V, GPIO.LOW)
        GPIO.output(PIN_hv50V, GPIO.LOW)
        GPIO.output(PIN_hv25V, GPIO.LOW)
        GPIO.output(PIN_hv12V, GPIO.LOW)
        GPIO.output(PIN_hv_connect_load, GPIO.LOW)
        self.selectedDriverStrength = DRIVER_STRENGTH_UNKNOWN


if __name__ == "__main__":
    print("Testing powersupply_dideboccs")
    psu = powersupplyInterface()
    for u in range(0, 410, 10):
        print("setting voltage to " + str(u) + " volts.")
        psu.setVoltage(u)
        for k in range(0, 10):
            sleep(0.5)
            uHvMeasured = psu.readPhysicalVoltage()
            print("uHvMeasured = {}".format(uHvMeasured))

    sleep(10)
    print("Finally setting voltage to 0.")
    psu.setVoltage(0)
