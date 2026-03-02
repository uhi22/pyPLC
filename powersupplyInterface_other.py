#
# Power supply interface for future extension
# Controls the high voltage power supply
#

#import Adafruit_BBIO.ADC as ADC
#import Adafruit_BBIO.GPIO as GPIO
from time import sleep


class powersupplyInterface():
    def setVoltage(self, targetVoltage):
        pass

    def readPhysicalVoltage(self):
        return 0
        
    def selectDriverForCableCheck(self):
        # very weak driver strengh, e.g. for cable check
        pass

    def selectDriverForPrecharge(self):
        pass
        
    def __init__(self):
        pass


if __name__ == "__main__":
    print("Testing powersupply")
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
