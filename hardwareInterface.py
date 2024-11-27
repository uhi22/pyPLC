
# For serial (including USB-to-serial) interfaces:
# https://pyserial.readthedocs.io/en/latest/pyserial.html
# Install pyserial library:
#   python -m pip install pyserial
# List ports:
#   python -m serial.tools.list_ports

import serial # the pyserial
from pyPlcModes import *
from serial.tools.list_ports import comports
from time import sleep, time
from configmodule import getConfigValue, getConfigValueBool
import sys # For exit_on_session_end hack

PinCp = "P9_41"
PinPowerRelay = "P9_17"

if (getConfigValue("digital_output_device")=="mqtt"):
    # If we use MQTT as a hardware interface import it here
    import paho.mqtt.client as mqtt

if (getConfigValue("digital_output_device")=="beaglebone"):
    # In case we run on beaglebone, we want to use GPIO ports.
    import Adafruit_BBIO.GPIO as GPIO

if (getConfigValue("charge_parameter_backend")=="chademo"):
    # In case we use the CHAdeMO backend, we want to use CAN
    import can

class hardwareInterface():
    def needsSerial(self):
        # Find out, whether we need a serial port. This depends on several configuration items.
        if (getConfigValueBool("display_via_serial")):
            return True # a display is expected to be connected to serial port.
        if (getConfigValue("digital_output_device")=="dieter"):
            return True # a "dieter" output device is expected to be connected on serial port.
        if (getConfigValue("analog_input_device")=="dieter"):
            return True # a "dieter" input device is expected to be connected on serial port.
        if (getConfigValue("digital_output_device")=="celeron55device"):
            return True
        if (getConfigValue("analog_input_device")=="celeron55device"):
            return True
        return False # non of the functionalities need a serial port.
        
    def findSerialPort(self):
        baud = int(getConfigValue("serial_baud"))
        if (getConfigValue("serial_port")!="auto"):
            port = getConfigValue("serial_port")
            try:
                self.addToTrace("Using serial port " + port)
                self.ser = serial.Serial(port, baud, timeout=0)
                self.isSerialInterfaceOk = True
            except:
                if (self.needsSerial()):
                    self.addToTrace("ERROR: Could not open serial port.")
                else:
                    self.addToTrace("Could not open serial port, but also do not need it. Ok.")
                self.ser = None
                self.isSerialInterfaceOk = False
            return

        ports = []
        self.addToTrace('Auto detection of serial ports. Available serial ports:')
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
                self.ser = serial.Serial(ports[0], baud, timeout=0)
                self.isSerialInterfaceOk = True
            except:
                self.addToTrace("ERROR: Could not open serial port.")
                self.ser = None
                self.isSerialInterfaceOk = False

    def addToTrace(self, s):
        self.callbackAddToTrace("[HARDWAREINTERFACE] " + s)            

    def displayState(self, state):
        if (getConfigValue("digital_output_device")=="mqtt"):
            self.mqttclient.publish(getConfigValue("mqtt_topic") + "/fsm_state", state)
    
    def displaySoc(self, soc):
        if getConfigValue("charge_parameter_backend") == "mqtt":
            self.mqttclient.publish(getConfigValue("mqtt_topic") + "/soc", str(soc))

    def setStateB(self):
        self.addToTrace("Setting CP line into state B.")
        if (getConfigValue("digital_output_device")=="beaglebone"):
            GPIO.output(PinCp, GPIO.LOW)
        if (getConfigValue("digital_output_device")=="celeron55device"):
            self.ser.write(bytes("cp=0\n", "utf-8"))
        if (getConfigValue("digital_output_device")=="mqtt"):
            self.mqttclient.publish(getConfigValue("mqtt_topic") + "/cpstate", "B")
        self.outvalue &= ~1
        
    def setStateC(self):
        self.addToTrace("Setting CP line into state C.")
        if (getConfigValue("digital_output_device")=="beaglebone"):
            GPIO.output(PinCp, GPIO.HIGH)
        if (getConfigValue("digital_output_device")=="celeron55device"):
            self.ser.write(bytes("cp=1\n", "utf-8"))
        if (getConfigValue("digital_output_device")=="mqtt"):
            self.mqttclient.publish(getConfigValue("mqtt_topic") + "/cpstate", "C")
        self.outvalue |= 1
        
    def setPowerRelayOn(self):
        self.addToTrace("Switching PowerRelay ON.")
        if (getConfigValue("digital_output_device")=="beaglebone"):
            GPIO.output(PinPowerRelay, GPIO.HIGH)
        if (getConfigValue("digital_output_device")=="celeron55device"):
            self.ser.write(bytes("contactor=1\n", "utf-8"))
        if (getConfigValue("digital_output_device")=="mqtt"):
            self.mqttclient.publish(getConfigValue("mqtt_topic") + "/relay_request", "on")
        self.outvalue |= 2

    def setPowerRelayOff(self):
        self.addToTrace("Switching PowerRelay OFF.")
        if (getConfigValue("digital_output_device")=="beaglebone"):
            GPIO.output(PinPowerRelay, GPIO.LOW)
        if (getConfigValue("digital_output_device")=="celeron55device"):
            self.ser.write(bytes("contactor=0\n", "utf-8"))
        if (getConfigValue("digital_output_device")=="mqtt"):
            self.mqttclient.publish(getConfigValue("mqtt_topic") + "/relay_request", "off")
        self.outvalue &= ~2

    def setRelay2On(self):
        self.addToTrace("Switching Relay2 ON.")
        self.outvalue |= 4

    def setRelay2Off(self):
        self.addToTrace("Switching Relay2 OFF.")
        self.outvalue &= ~4
        
    def getPowerRelayConfirmation(self):
        if (getConfigValue("digital_output_device")=="celeron55device"):
            return self.contactor_confirmed
        return 1 # todo: self.contactor_confirmed
        
    def triggerConnectorLocking(self):
        self.addToTrace("Locking the connector")
        if (getConfigValue("digital_output_device")=="celeron55device"):
            self.ser.write(bytes("lock\n", "utf-8"))
        if (getConfigValue("digital_output_device")=="mqtt"):
            self.mqttclient.publish(getConfigValue("mqtt_topic") + "/lock_request", "lock")
        # todo control the lock motor into lock direction until the end (time based or current based stopping?)

    def triggerConnectorUnlocking(self):
        self.addToTrace("Unlocking the connector")
        if (getConfigValue("digital_output_device")=="celeron55device"):
            self.ser.write(bytes("unlock\n", "utf-8"))
        if (getConfigValue("digital_output_device")=="mqtt"):
            self.mqttclient.publish(getConfigValue("mqtt_topic") + "/lock_request", "unlock")
        # todo control the lock motor into unlock direction until the end (time based or current based stopping?)

    def isConnectorLocked(self):
        # TODO: Read the lock= value from the hardware so that this works
        #if (getConfigValue("digital_output_device")=="celeron55device"):
        #    return self.lock_confirmed
        return 1 # todo: use the real connector lock feedback
        
    def setChargerParameters(self, maxVoltage, maxCurrent):
        self.addToTrace("Setting charger parameters maxVoltage=%d V, maxCurrent=%d A" % (maxVoltage, maxCurrent))
        self.maxChargerVoltage = int(maxVoltage)
        self.maxChargerCurrent = int(maxCurrent)
        if getConfigValue("charge_parameter_backend") == "mqtt":
            self.mqttclient.publish(getConfigValue("mqtt_topic") + "/charger_max_voltage", str(maxVoltage))
            self.mqttclient.publish(getConfigValue("mqtt_topic") + "/charger_max_current", str(maxCurrent))
        
    def setChargerVoltageAndCurrent(self, voltageNow, currentNow):
        self.addToTrace("Setting charger present values Voltage=%d V, Current=%d A" % (voltageNow, currentNow))
        self.chargerVoltage = int(voltageNow)
        self.chargerCurrent = int(currentNow)

        if getConfigValue("charge_parameter_backend") == "mqtt":
            self.mqttclient.publish(getConfigValue("mqtt_topic") + "/charger_voltage", voltageNow)
            self.mqttclient.publish(getConfigValue("mqtt_topic") + "/charger_current", currentNow)
        
    def setPowerSupplyVoltageAndCurrent(self, targetVoltage, targetCurrent):
        # if we are the charger, and have a real power supply which we want to control, we do it here
        self.homeplughandler.sendSpecialMessageToControlThePowerSupply(targetVoltage, targetCurrent)
        #here we can publish the voltage and current requests received from the PEV side
        if getConfigValue("charge_parameter_backend") == "mqtt":
            self.mqttclient.publish(getConfigValue("mqtt_topic") + "/target_voltage", str(targetVoltage))
            self.mqttclient.publish(getConfigValue("mqtt_topic") + "/target_current", str(targetCurrent))

    def getInletVoltage(self):
        # uncomment this line, to take the simulated inlet voltage instead of the really measured
        # self.inletVoltage = self.simulatedInletVoltage
        return self.inletVoltage
        
    def getAccuVoltage(self):
        if getConfigValue("charge_parameter_backend") in ["chademo", "mqtt", "celeron55device"]:
           return self.accuVoltage 
        #todo: get real measured voltage from the accu
        self.accuVoltage = 230
        return self.accuVoltage

    def getAccuMaxCurrent(self):
        if (getConfigValue("digital_output_device")=="celeron55device"):
            # The overall current limit is currently hardcoded in
            # OpenV2Gx/src/test/main_commandlineinterface.c
            EVMaximumCurrentLimit = 250
            if self.accuMaxCurrent >= EVMaximumCurrentLimit:
                return EVMaximumCurrentLimit
            return self.accuMaxCurrent
        elif getConfigValue("charge_parameter_backend") in ["chademo", "mqtt"]:
            return self.accuMaxCurrent #set by CAN or MQTT
        #todo: get max charging current from the BMS
        self.accuMaxCurrent = 10
        return self.accuMaxCurrent

    def getAccuMaxVoltage(self):
        if getConfigValue("charge_parameter_backend") in ["chademo", "mqtt"]:
            return self.accuMaxVoltage #set by CAN or MQTT
        elif getConfigValue("charge_target_voltage"):
            self.accuMaxVoltage = getConfigValue("charge_target_voltage")            
        else:
            #todo: get max charging voltage from the BMS
            self.accuMaxVoltage = 230
        return self.accuMaxVoltage

    def getIsAccuFull(self):
        if (getConfigValue("digital_output_device")=="celeron55device"):
            self.IsAccuFull = (self.soc_percent >= 98)
        else:
            #todo: get "full" indication from the BMS
            self.IsAccuFull = (self.simulatedSoc >= 98)
        return self.IsAccuFull

    def getSoc(self):
        if self.callbackShowStatus:
            self.callbackShowStatus(format(self.soc_percent,".1f"), "soc")
        if (getConfigValue("digital_output_device") in ["celeron55device", "mqtt"]):
            return self.soc_percent
        #todo: get SOC from the BMS
        self.callbackShowStatus(format(self.simulatedSoc,".1f"), "soc")
        return self.simulatedSoc

    def stopRequest(self):
        return not self.enabled
    
    def isUserAuthenticated(self):
        # If the user needs to authorize, fill this function in a way that it returns False as long as
        # we shall wait for the users authorization, and returns True if the authentication was successfull.
        # Discussing here: https://github.com/uhi22/pyPLC/issues/28#issuecomment-2230656379
        # For testing purposes, we just use a counter to decide that we return
        # once "ongoing" and then "finished".
        if (self.demoAuthenticationCounter<1):
            self.demoAuthenticationCounter += 1
            return False
        else:
            return True

    def initPorts(self):
        if (getConfigValue("charge_parameter_backend") == "chademo"):
            filters = [
               {"can_id": 0x100, "can_mask": 0x7FF, "extended": False},
               {"can_id": 0x101, "can_mask": 0x7FF, "extended": False},
               {"can_id": 0x102, "can_mask": 0x7FF, "extended": False}]
            self.canbus = can.interface.Bus(bustype='socketcan', channel="can0", can_filters = filters)
    
        if (getConfigValue("digital_output_device") == "beaglebone"):
            # Port configuration according to https://github.com/jsphuebner/pyPLC/commit/475f7fe9f3a67da3d4bd9e6e16dfb668d0ddb1d6
            GPIO.setup(PinPowerRelay, GPIO.OUT) #output for port relays
            GPIO.setup(PinCp, GPIO.OUT) #output for CP
            
        if (getConfigValue("digital_output_device") == "mqtt"):
        	self.mqttclient = mqtt.Client(client_id="pyplc")
        	self.mqttclient.on_connect = self.mqtt_on_connect
        	self.mqttclient.on_disconnect = self.mqtt_on_disconnect
        	self.mqttclient.on_message = self.mqtt_on_message
        	self.mqttclient.connect(getConfigValue("mqtt_broker"), 1883, 60)
        
    def __init__(self, callbackAddToTrace=None, callbackShowStatus=None, homeplughandler=None, mode=C_EVSE_MODE):
        self.callbackAddToTrace = callbackAddToTrace
        self.callbackShowStatus = callbackShowStatus
        self.homeplughandler = homeplughandler
        self.mode = mode

        self.loopcounter = 0
        self.outvalue = 0
        self.simulatedSoc = 20.0 # percent
        self.demoAuthenticationCounter = 0
        self.enabled = True #Charging enabled

        self.inletVoltage = 0.0 # voltsringbuffer
        self.accuVoltage = 0.0
        self.lock_confirmed = False  # Confirmation from hardware
        self.cp_pwm = 0.0
        self.soc_percent = 0.0
        self.capacity = 0.0
        self.accuMaxVoltage = 0.0
        self.accuMaxCurrent = 0.0
        self.contactor_confirmed = False  # Confirmation from hardware
        self.plugged_in = None  # None means "not known yet"
        self.lastReceptionTime = 0

        self.maxChargerVoltage = 0
        self.maxChargerCurrent = 10
        self.chargerVoltage = 0
        self.chargerCurrent = 0

        self.logged_inlet_voltage = None
        self.logged_dc_link_voltage = None
        self.logged_cp_pwm = None
        self.logged_max_charge_a = None
        self.logged_soc_percent = None
        self.logged_contactor_confirmed = None
        self.logged_plugged_in = None

        self.rxbuffer = ""

        self.findSerialPort()
        self.initPorts()
        
    def resetSimulation(self):
        self.simulatedInletVoltage = 0.0 # volts
        self.simulatedSoc = 20.0 # percent
        self.demoAuthenticationCounter = 0
        
    def simulatePreCharge(self):
        if (self.simulatedInletVoltage<230):
            self.simulatedInletVoltage = self.simulatedInletVoltage + 1.0 # simulate increasing voltage during PreCharge

    def close(self):
        if (self.isSerialInterfaceOk):        
            self.ser.close()

    def evaluateReceivedData_dieter(self, s):
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

    def evaluateReceivedData_celeron55device(self, s):
        self.rxbuffer += s
        while True:
            x = self.rxbuffer.find("\n")
            if x < 0:
                break
            line = self.rxbuffer[0:x].strip()
            self.rxbuffer = self.rxbuffer[x+1:]
            #self.addToTrace("Received line: \""+line+"\"")
            if line.startswith("inlet_v="):
                self.inletVoltage = int(line[8:])
                if self.logged_inlet_voltage != self.inletVoltage:
                    self.logged_inlet_voltage = self.inletVoltage
                    self.addToTrace("<< inlet_voltage="+str(self.inletVoltage))
                if self.callbackShowStatus:
                    self.callbackShowStatus(format(self.inletVoltage,".1f"), "uInlet")
            elif line.startswith("dc_link_v="):
                self.accuVoltage = int(line[10:])
                if self.logged_dc_link_voltage != self.accuVoltage:
                    self.logged_dc_link_voltage = self.accuVoltage
                    self.addToTrace("<< dc_link_voltage="+str(self.accuVoltage))
            elif line.startswith("cp_pwm="):
                self.cp_pwm = int(line[7:])
                if self.logged_cp_pwm != self.cp_pwm:
                    self.logged_cp_pwm = self.cp_pwm
                    self.addToTrace("<< cp_pwm="+str(self.cp_pwm))
            elif line.startswith("cp_output_state="):
                state = int(line[len("cp_output_state="):])
                if bool(state) == ((self.outvalue & 1)!=0):
                    self.addToTrace("<< CP state confirmed")
                else:
                    self.addToTrace("<< CP state MISMATCH")
            elif line.startswith("ccs_contactor_wanted_closed="):
                state = int(line[len("ccs_contactor_wanted_closed="):])
                if bool(state) == ((self.outvalue & 2)!=0):
                    self.addToTrace("<< Contactor request confirmed")
                else:
                    self.addToTrace("<< Contactor request MISMATCH")
            elif line.startswith("max_charge_a="):
                self.accuMaxCurrent = int(line[13:])
                if self.logged_max_charge_a != self.accuMaxCurrent:
                    self.logged_max_charge_a = self.accuMaxCurrent
                    self.addToTrace("<< max_charge_a="+str(self.accuMaxCurrent))
            elif line.startswith("soc_percent="):
                self.soc_percent = int(line[12:])
                if self.logged_soc_percent != self.soc_percent:
                    self.logged_soc_percent = self.soc_percent
                    self.addToTrace("<< soc_percent="+str(self.soc_percent))
            elif line.startswith("contactor_confirmed="):
                self.contactor_confirmed = bool(int(line[20:]))
                if self.logged_contactor_confirmed != self.contactor_confirmed:
                    self.logged_contactor_confirmed = self.contactor_confirmed
                    self.addToTrace("<< contactor_confirmed="+str(self.contactor_confirmed))
            elif line.startswith("plugged_in="):
                self.plugged_in = bool(int(line[11:]))
                if self.logged_plugged_in != self.plugged_in:
                    self.logged_plugged_in = self.plugged_in
                    self.addToTrace("<< plugged_in="+str(self.plugged_in))
            else:
                self.addToTrace("Received unknown line: \""+line+"\"")

    def showOnDisplay(self, s1, s2, s3):
        # show the given string s on the display which is connected to the serial port
        if (getConfigValueBool("display_via_serial") and self.isSerialInterfaceOk):
            if (getConfigValue("digital_output_device")=="celeron55device"):
                s = "disp0=" + s1 + "\n" + "disp1=" + s2 + "\n" + "disp2=" + s3 + "\n"
                self.ser.write(bytes(s, "utf-8"))
            else:
                s = "lc" + s1 + "\n" + "lc" + s2 + "\n" + "lc" + s3 + "\n"
                self.ser.write(bytes(s, "utf-8"))
        
    def mainfunction(self):
        if (getConfigValueBool("soc_simulation")):
            if (self.simulatedSoc<100):
                if ((self.outvalue & 2)!=0):
                    # while the relay is closed, simulate increasing SOC
                    deltaSoc = 0.5 # how fast the simulated SOC shall rise.
                    # Examples:
                    #  0.01 charging needs some minutes, good for light bulb tests
                    #  0.5 charging needs ~8s, good for automatic test case runs.
                    self.simulatedSoc = self.simulatedSoc + deltaSoc
                
        if (getConfigValue("charge_parameter_backend")=="chademo"):
           self.mainfunction_chademo()
        
        if (getConfigValue("digital_output_device")=="dieter"):
            self.mainfunction_dieter()

        if (getConfigValue("digital_output_device")=="celeron55device"):
            self.mainfunction_celeron55device()

        if (getConfigValue("digital_output_device")=="mqtt"):
            self.mainfunction_mqtt()

        if getConfigValueBool("exit_on_session_end"):
            # TODO: This is a hack. Do this in fsmPev instead and publish some
            # of these values into there if needed.
            if (self.plugged_in is not None and self.plugged_in == False and
                    self.inletVoltage < 50):
                sys.exit(0)

    def mainfunction_dieter(self):
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
                self.evaluateReceivedData_dieter(s)

    def mainfunction_celeron55device(self):
        if (self.isSerialInterfaceOk):
            s = self.ser.read(100)
            if (len(s)>0):
                try:
                    s = str(s, 'utf-8')
                except:
                    s = "" # for the case we received corrupted data (not convertable as utf-8)
                #self.addToTrace(str(len(s)) + " bytes received: " + s)
                self.evaluateReceivedData_celeron55device(s)
                
    def mainfunction_chademo(self):
       message = self.canbus.recv(0)
       
       if message:
          if message.arbitration_id == 0x100:
             vtg = (message.data[1] << 8) + message.data[0]
             if self.accuVoltage != vtg:
                 self.addToTrace("CHAdeMO: Set battery voltage to %d V" % vtg)
             self.accuVoltage = vtg
             if self.capacity != message.data[6]:
                 self.addToTrace("CHAdeMO: Set capacity to %d" % message.data[6])
             self.capacity = message.data[6]
             
             msg = can.Message(arbitration_id=0x108, data=[ 0, self.maxChargerVoltage & 0xFF, self.maxChargerVoltage >> 8, self.maxChargerCurrent, 0, 0, 0, 0], is_extended_id=False)
             self.canbus.send(msg)
             #Report unspecified version 10, this makes our custom implementation send the momentary
             #battery voltage in 0x100 bytes 0 and 1
             status = 4 if self.maxChargerVoltage > 0 else 0  #report connector locked
             msg = can.Message(arbitration_id=0x109, data=[ 10, self.chargerVoltage & 0xFF, self.chargerVoltage >> 8, self.chargerCurrent, 0, status, 0, 0], is_extended_id=False)
             self.canbus.send(msg)
             
          if message.arbitration_id == 0x102:
             vtg = (message.data[2] << 8) + message.data[1]
             if self.accuMaxVoltage != vtg:
                 self.addToTrace("CHAdeMO: Set target voltage to %d V" % vtg)
             self.accuMaxVoltage = vtg
             
             if self.accuMaxCurrent != message.data[3]:
                 self.addToTrace("CHAdeMO: Set current request to %d A" % message.data[3])
             self.accuMaxCurrent = message.data[3]
             self.lastReceptionTime = time()
             
             if self.capacity > 0:
                 soc = message.data[6] / self.capacity * 100
                 if self.simulatedSoc != soc:
                     self.addToTrace("CHAdeMO: Set SoC to %d %%" % soc)
                 self.simulatedSoc = soc
       #if nothing was received for over a second, time out        
       if self.lastReceptionTime < (time() - 1):
           if self.accuMaxCurrent != 0:
              self.addToTrace("CHAdeMO: No current limit update for over 1s, setting current to 0")
           self.accuMaxCurrent = 0
           
    def mainfunction_mqtt(self):
        self.mqttclient.loop(timeout=0.1)
        
    def mqtt_on_disconnect(self, client, userdata, rc):
        self.addToTrace(f"MQTT disconnected with result code {rc}")
        self.mqttclient.connect(getConfigValue("mqtt_broker"), 1883, 60)
	
	# The callback for when the client receives a CONNACK response from the server.
    def mqtt_on_connect(self, client, userdata, flags, rc):
        self.addToTrace(f"MQTT connected with result code {rc}")

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        if self.mode == C_EVSE_MODE:
            client.subscribe(getConfigValue("mqtt_topic") + "/charger_max_voltage") #todo
            client.subscribe(getConfigValue("mqtt_topic") + "/charger_max_current") #todo
            client.subscribe(getConfigValue("mqtt_topic") + "/charger_voltage")
            client.subscribe(getConfigValue("mqtt_topic") + "/charger_current")
            client.subscribe(getConfigValue("mqtt_topic") + "/enabled")
        elif self.mode == C_PEV_MODE:
            client.subscribe(getConfigValue("mqtt_topic") + "/battery_voltage")
            client.subscribe(getConfigValue("mqtt_topic") + "/target_voltage")
            client.subscribe(getConfigValue("mqtt_topic") + "/target_current")
            client.subscribe(getConfigValue("mqtt_topic") + "/soc")
            client.subscribe(getConfigValue("mqtt_topic") + "/inlet_voltage")

    def mqtt_on_message(self, client, userdata, msg):
        baseTopic = getConfigValue("mqtt_topic")
        
        if msg.topic == (f"{baseTopic}/battery_voltage"):
            self.accuVoltage = float(msg.payload)
            self.addToTrace("MQTT: Set battery voltage to %f V" % self.accuVoltage)
        elif msg.topic == (f"{baseTopic}/target_voltage"):
            self.accuMaxVoltage = float(msg.payload)
            self.addToTrace("MQTT: Set target voltage to %f V" % self.accuMaxVoltage)
        elif msg.topic == (f"{baseTopic}/target_current") or msg.topic == (f"{baseTopic}/charger_current"):
            self.accuMaxCurrent = float(msg.payload)
            self.addToTrace("MQTT: Set current request to %s A" % self.accuMaxCurrent)
        elif msg.topic == (f"{baseTopic}/soc"):
            self.simulatedSoc = float(msg.payload)
            self.soc_percent = self.simulatedSoc
            self.addToTrace("MQTT: Set SoC to %f %%" % self.simulatedSoc)
        elif msg.topic == (f"{baseTopic}/inlet_voltage") or msg.topic == (f"{baseTopic}/charger_voltage"):
            self.inletVoltage = float(msg.payload) #in EVSE mode this is present charger voltage
            self.addToTrace("MQTT: Set present voltage to %f V" % self.inletVoltage)
        elif msg.topic == (f"{baseTopic}/enabled"):
            self.enabled = bool(int(msg.payload))
            self.addToTrace("MQTT: Setting enable flag to %d" % self.enabled)

def myPrintfunction(s):
    print("myprint " + s)

if __name__ == "__main__":
    print("Testing hardwareInterface...")
    hw = hardwareInterface(myPrintfunction)
    for i in range(0, 350):
        hw.mainfunction()
        if (i==20):
            hw.showOnDisplay("Hello", "A DEMO", "321.0V")
            hw.setChargerParameters(500, 125)
            hw.setChargerVoltageAndCurrent(360, 100)
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
        sleep(0.01)
    hw.close()    
    print("finished.")
