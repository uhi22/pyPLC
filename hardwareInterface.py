
# For serial (including USB-to-serial) interfaces:
# https://pyserial.readthedocs.io/en/latest/pyserial.html
# Install pyserial library:
#   python -m pip install pyserial
# List ports:
#   python -m serial.tools.list_ports

import serial # the pyserial
from serial.tools.list_ports import comports
from time import sleep

class hardwareInterface():
    def findSerialPort(self):
        ports = []
        self.addToTrace('Available serial ports:')
        for n, (port, desc, hwid) in enumerate(sorted(comports()), 1):
            self.addToTrace('{:2}: {:20} {!r}'.format(n, port, desc))
            ports.append(port)
        if (len(ports)<1):
            self.addToTrace("ERROR: No serial ports found. No hardware interaction possible.")
            self.ser = None
            self.isInterfaceOk = False
        else:
            self.addToTrace("ok, we take the first port, " + ports[0])
            try:
                self.ser = serial.Serial(ports[0], 19200, timeout=0)
                self.isInterfaceOk = True
            except:
                self.addToTrace("ERROR: Could not open serial port.")
                self.ser = None
                self.isInterfaceOk = False

    def addToTrace(self, s):
        self.callbackAddToTrace("[HARDWAREINTERFACE] " + s)            

    def setStateB(self):
        self.addToTrace("Setting CP line into state B.")
        self.outvalue &= ~1
        
    def setStateC(self):
        self.addToTrace("Setting CP line into state C.")
        self.outvalue |= 1
        
    def setPowerRelayOn(self):
        self.addToTrace("Switching PowerRelay ON.")
        self.outvalue |= 2

    def setPowerRelayOff(self):
        self.addToTrace("Switching PowerRelay OFF.")
        self.outvalue &= ~2

    def setRelay2On(self):
        self.addToTrace("Switching PowerRelay ON.")
        self.outvalue |= 4

    def setRelay2Off(self):
        self.addToTrace("Switching PowerRelay OFF.")
        self.outvalue &= ~4
        
    def getInletVoltage(self):
        #todo: get real measured voltage from the inlet
        self.inletVoltage = self.simulatedInletVoltage
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
        return self.simulatedSoc
        
        
    def __init__(self, callbackAddToTrace=None):
        self.callbackAddToTrace = callbackAddToTrace
        self.loopcounter = 0
        self.outvalue = 0
        self.simulatedSoc = 20.0 # percent
        self.inletVoltage = 0.0 # volts
        self.findSerialPort()
        
    def resetSimulation(self):
        self.simulatedInletVoltage = 0.0 # volts
        self.simulatedSoc = 20.0 # percent
        
    def simulatePreCharge(self):
        if (self.simulatedInletVoltage<230):
            self.simulatedInletVoltage = self.simulatedInletVoltage + 1.0 # simulate increasing voltage during PreCharge

    def close(self):
        if (self.isInterfaceOk):        
            self.ser.close()
    
    def mainfunction(self):
        if (self.simulatedSoc<100):
            if ((self.outvalue & 2)!=0):
                # while the relay is closed, simulate increasing SOC
                self.simulatedSoc = self.simulatedSoc + 0.05
        self.loopcounter+=1
        if (self.isInterfaceOk):
            if (self.loopcounter>15):
                self.loopcounter=0
                # self.ser.write(b'hello world\n')
                s = "000" + str(self.outvalue)
                self.ser.write(bytes("do"+s+"\n", "utf-8")) # set outputs of dieter, see https://github.com/uhi22/dieter
            s = self.ser.read(100)
            if (len(s)>0):
                self.addToTrace(str(len(s)) + " bytes received: " + str(s, 'utf-8').strip())
        
def myPrintfunction(s):
    print("myprint " + s)

if __name__ == "__main__":
    print("Testing hardwareInterface...")
    hw = hardwareInterface(myPrintfunction)
    for i in range(0, 350):
        hw.mainfunction()
        if (i==50):
            hw.setStateC()
        if (i==100):
            hw.setStateB()
        if (i==150):
            hw.setStateC()
            hw.setPowerRelayOn()
        if (i==200):
            hw.setStateB()
            hw.setPowerRelayOff()
        if (i==250):
            hw.setRelay2On()
        if (i==300):
            hw.setRelay2Off()
        sleep(0.03)
    hw.close()    
    print("finished.")