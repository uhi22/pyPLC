# State machine for the charger
#
#

#------------------------------------------------------------

import pyPlcTcpSocket
import time # for time.sleep()

stateWaitForSupportedApplicationProtocolRequest = 0
stateWaitForSessionSetupRequest = 1
stateWaitForServiceDiscoveryRequest = 2
stateWaitForPaymentServiceSelectionRequest = 3
stateWaitForAuthorizationRequest = 4
stateWaitForChargeParameterRequest = 5
stateWaitForCableCheckRequest = 6
stateWaitForPreChargeRequest = 7
stateWaitForPowerDeliveryRequest = 8

class fsmEvse():
    def enterState(self, n):
        print("from " + str(self.state) + " entering " + str(n))
        self.state = n
        self.cyclesInState = 0
        
    def isTooLong(self):
        # The timeout handling function.
        return (self.cyclesInState > 20)
        
        
    def stateFunctionWaitForSupportedApplicationProtocolRequest(self):
        if (len(self.rxData)>0):
            msg = "ok, you sent " + str(self.rxData) 
            self.rxData = []
            print("responding " + msg)
            self.Tcp.transmit(bytes(msg, "utf-8"))
            self.enterState(1)
        
    def stateFunctionWaitForSessionSetupRequest(self):
        if (len(self.rxData)>0):
            self.rxData = []
            self.enterState(2)
        if (self.isTooLong()):
            self.enterState(0)
            
    def stateFunctionWaitForServiceDiscoveryRequest(self):
        if (len(self.rxData)>0):
            self.rxData = []
            self.enterState(3)
        if (self.isTooLong()):
            self.enterState(0)
            
    def stateFunctionWaitForPaymentServiceSelectionRequest(self):
        if (len(self.rxData)>0):
            self.rxData = []
            self.enterState(4)
        if (self.isTooLong()):
            self.enterState(0)
            
    def stateFunctionWaitForAuthorizationRequest(self):
        if (len(self.rxData)>0):
            self.rxData = []
            self.enterState(5)
        if (self.isTooLong()):
            self.enterState(0)
            
    def stateFunctionWaitForChargeParameterRequest(self):
        if (len(self.rxData)>0):
            self.rxData = []
            self.enterState(6)
        if (self.isTooLong()):
            self.enterState(0)
            
    def stateFunctionWaitForCableCheckRequest(self):
        if (len(self.rxData)>0):
            self.rxData = []
            self.enterState(7)
        if (self.isTooLong()):
            self.enterState(0)
            
    def stateFunctionWaitForPreChargeRequest(self):
        if (len(self.rxData)>0):
            self.rxData = []
            self.enterState(8)
        if (self.isTooLong()):
            self.enterState(0)
            
    def stateFunctionWaitForPowerDeliveryRequest(self):
        if (len(self.rxData)>0):
            self.rxData = []
            self.enterState(0)
        if (self.isTooLong()):
            self.enterState(0)
            
       
    stateFunctions = { 
            stateWaitForSupportedApplicationProtocolRequest: stateFunctionWaitForSupportedApplicationProtocolRequest,
            stateWaitForSessionSetupRequest: stateFunctionWaitForSessionSetupRequest,
            stateWaitForServiceDiscoveryRequest: stateFunctionWaitForServiceDiscoveryRequest,
            stateWaitForPaymentServiceSelectionRequest: stateFunctionWaitForPaymentServiceSelectionRequest,
            stateWaitForAuthorizationRequest: stateFunctionWaitForAuthorizationRequest,
            stateWaitForChargeParameterRequest: stateFunctionWaitForChargeParameterRequest,
            stateWaitForCableCheckRequest: stateFunctionWaitForCableCheckRequest,
            stateWaitForPreChargeRequest: stateFunctionWaitForPreChargeRequest,
            stateWaitForPowerDeliveryRequest: stateFunctionWaitForPowerDeliveryRequest,
        }
        
    def reInit(self):
        print("re-initializing fsmEvse") 
        self.state = 0
        self.cyclesInState = 0
        self.rxData = []

    def __init__(self):
        print("initializing fsmEvse") 
        self.Tcp = pyPlcTcpSocket.pyPlcTcpServerSocket()
        self.state = 0
        self.cyclesInState = 0
        self.rxData = []
                
    def mainfunction(self):
        self.Tcp.mainfunction() # call the lower-level worker
        if (self.Tcp.isRxDataAvailable()):
                self.rxData = self.Tcp.getRxData()
                print("received " + str(self.rxData))
                #msg = "ok, you sent " + str(self.rxData)
                #print("responding " + msg)
                #self.Tcp.transmit(bytes(msg, "utf-8"))
        # run the state machine:
        self.cyclesInState += 1 # for timeout handling, count how long we are in a state
        self.stateFunctions[self.state](self)
                
                
if __name__ == "__main__":
    print("Testing the evse state machine")
    evse = fsmEvse()
    print("Press Ctrl-Break for aborting")
    while (True):
        time.sleep(0.1)
        evse.mainfunction()
        

