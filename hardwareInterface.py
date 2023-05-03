
# For serial (including USB-to-serial) interfaces:
# https://pyserial.readthedocs.io/en/latest/pyserial.html
# Install pyserial library:
#   python -m pip install pyserial
# List ports:
#   python -m serial.tools.list_ports

import serial # the pyserial
from serial.tools.list_ports import comports
from time import sleep
from configmodule import getConfigValue, getConfigValueBool

if (getConfigValue("digital_output_device")=="beaglebone"):
    # In case we run on beaglebone, we want to use GPIO ports.
    import Adafruit_BBIO.GPIO as GPIO

class hardwareInterface():
    def needsSerial(self):
        # Find out, whether we need a serial port. This depends on several configuration items.
        if (getConfigValueBool("display_via_serial")):
            return True # a display is expected to be connected to serial port.
        if (getConfigValue("digital_output_device")=="dieter"):
            return True # a "dieter" output device is expected to be connected on serial port.
        if (getConfigValue("analog_input_device")=="dieter"):
            return True # a "dieter" input device is expected to be connected on serial port.
        return False # non of the functionalities need a serial port.
        
    def findSerialPort(self):
        ports = []
        self.addToTrace('Available serial ports:')
        for n, (port, desc, hwid) in enumerate(sorted(comports()), 1):
            if (port=="/dev/ttyAMA0"):
                self.addToTrace("ignoring /dev/ttyAMA0, because this is not an USB serial port")
            else:
                self.addToTrace('{:2}: {:20} {!r}'.format(n, port, desc))
                ports.append(port)
        if (len(ports)<1):
            if (self.needsSerial()):
                self.addToTrace("ERROR: No serial ports found. No hardware interaction possible.")
                self.ser = None
                self.isSerialInterfaceOk = False
            else:
                self.addToTrace("We found no serial port, but also do not need it. No problem.")
                self.ser = None
                self.isSerialInterfaceOk = False
        else:
            self.addToTrace("ok, we take the first port, " + ports[0])
            try:
                self.ser = serial.Serial(ports[0], 19200, timeout=0)
                self.isSerialInterfaceOk = True
            except:
                self.addToTrace("ERROR: Could not open serial port.")
                self.ser = None
                self.isSerialInterfaceOk = False

    def addToTrace(self, s):
        self.callbackAddToTrace("[HARDWAREINTERFACE] " + s)            

    def setStateB(self):
        self.addToTrace("Setting CP line into state B.")
        if (getConfigValue("digital_output_device")=="beaglebone"):
            GPIO.output("P8_18", GPIO.LOW)
        self.outvalue &= ~1
        
    def setStateC(self):
        self.addToTrace("Setting CP line into state C.")
        if (getConfigValue("digital_output_device")=="beaglebone"):
            GPIO.output("P8_18", GPIO.HIGH)
        self.outvalue |= 1
        
    def setPowerRelayOn(self):
        self.addToTrace("Switching PowerRelay ON.")
        if (getConfigValue("digital_output_device")=="beaglebone"):
            GPIO.output("P8_16", GPIO.HIGH)
        self.outvalue |= 2

    def setPowerRelayOff(self):
        self.addToTrace("Switching PowerRelay OFF.")
        if (getConfigValue("digital_output_device")=="beaglebone"):
            GPIO.output("P8_16", GPIO.LOW)
        self.outvalue &= ~2

    def setRelay2On(self):
        self.addToTrace("Switching Relay2 ON.")
        self.outvalue |= 4

    def setRelay2Off(self):
        self.addToTrace("Switching Relay2 OFF.")
        self.outvalue &= ~4
        
    def getPowerRelayConfirmation(self):
        return 1 # todo: self.contactor_confirmed

    def getInletVoltage(self):
        # uncomment this line, to take the simulated inlet voltage instead of the really measured
        # self.inletVoltage = self.simulatedInletVoltage
        return self.inletVoltage
        
    def getAccuVoltage(self):
        #todo: get real measured voltage from the accu
        self.accuVoltage = 230
        return self.accuVoltage

    def getAccuMaxCurrent(self):
        #todo: get max charging current from the BMS
        self.accuMaxCurrent = 10
        return self.accuMaxCurrent

    def getAccuMaxVoltage(self):
        #todo: get max charging voltage from the BMS
        self.accuMaxVoltage = 230
        return self.accuMaxVoltage

    def getIsAccuFull(self):
        #todo: get "full" indication from the BMS
        self.IsAccuFull = (self.simulatedSoc >= 98)
        return self.IsAccuFull

    def getSoc(self):
        #todo: get SOC from the BMS
        self.callbackShowStatus(format(self.simulatedSoc,".1f"), "soc")
        return self.simulatedSoc

    def initPorts(self):
        if (getConfigValue("digital_output_device") == "beaglebone"):
            # Port configuration according to https://github.com/jsphuebner/pyPLC/commit/475f7fe9f3a67da3d4bd9e6e16dfb668d0ddb1d6
            GPIO.setup("P8_16", GPIO.OUT) #output for port relays
            GPIO.setup("P8_18", GPIO.OUT) #output for CP
        
    def __init__(self, callbackAddToTrace=None, callbackShowStatus=None):
        self.callbackAddToTrace = callbackAddToTrace
        self.callbackShowStatus = callbackShowStatus
        self.loopcounter = 0
        self.outvalue = 0
        self.simulatedSoc = 20.0 # percent
        self.inletVoltage = 0.0 # volts
        self.rxbuffer = ""
        self.findSerialPort()
        self.initPorts()
            
        
    def resetSimulation(self):
        self.simulatedInletVoltage = 0.0 # volts
        self.simulatedSoc = 20.0 # percent
        
    def simulatePreCharge(self):
        if (self.simulatedInletVoltage<230):
            self.simulatedInletVoltage = self.simulatedInletVoltage + 1.0 # simulate increasing voltage during PreCharge

    def close(self):
        if (self.isSerialInterfaceOk):        
            self.ser.close()
            
    def evaluateReceivedData(self, s):
        self.rxbuffer += s
        x=self.rxbuffer.find("A0=")
        if (x>=0):
            s = self.rxbuffer[x+3:x+7]
            if (len(s)==4):
                try:
                    self.inletVoltage = int(s) / 1024.0 * 1.08 * (6250) / (4.7+4.7)
                    if (getConfigValue("analog_input_device")=="dieter"):
                        self.callbackShowStatus(format(self.inletVoltage,".1f"), "uInlet")
                except:
                    # keep last known value, if nothing new valid was received.
                    pass
                #self.addToTrace("RX data ok " + s)
                self.rxbuffer = self.rxbuffer[x+3:] # consume the receive buffer entry

    def showOnDisplay(self, s1, s2, s3):
        # show the given string s on the display which is connected to the serial port
        if (getConfigValueBool("display_via_serial") and self.isSerialInterfaceOk):
            s = "lc" + s1 + "\n" + "lc" + s2 + "\n" + "lc" + s3 + "\n"
            self.ser.write(bytes(s, "utf-8"))
        
    def mainfunction(self):
        if (getConfigValueBool("soc_simulation")):
            if (self.simulatedSoc<100):
                if ((self.outvalue & 2)!=0):
                    # while the relay is closed, simulate increasing SOC
                    self.simulatedSoc = self.simulatedSoc + 0.01
                
                
        self.loopcounter+=1
        if (self.isSerialInterfaceOk):
            if (self.loopcounter>15):
                self.loopcounter=0
                # self.ser.write(b'hello world\n')
                s = "000" + str(self.outvalue)
                self.ser.write(bytes("do"+s+"\n", "utf-8")) # set outputs of dieter, see https://github.com/uhi22/dieter
            s = self.ser.read(100)
            if (len(s)>0):
                try:
                    s = str(s, 'utf-8').strip()
                except:
                    s = "" # for the case we received corrupted data (not convertable as utf-8)
                self.addToTrace(str(len(s)) + " bytes received: " + s)
                self.evaluateReceivedData(s)
        
def myPrintfunction(s):
    print("myprint " + s)

if __name__ == "__main__":
    print("Testing hardwareInterface...")
    hw = hardwareInterface(myPrintfunction)
    for i in range(0, 350):
        hw.mainfunction()
        if (i==20):
            hw.showOnDisplay("Hello", "A DEMO", "321.0V")
        if (i==50):
            hw.setStateC()
        if (i==100):
            hw.setStateB()
        if (i==150):
            hw.setStateC()
            hw.setPowerRelayOn()
            hw.showOnDisplay("", "..middle..", "")
        if (i==200):
            hw.setStateB()
            hw.setPowerRelayOff()
        if (i==250):
            hw.setRelay2On()
        if (i==300):
            hw.setRelay2Off()
        if (i==320):
            hw.showOnDisplay("This", "...is...", "DONE :-)")
        sleep(0.03)
    hw.close()    
    print("finished.")
