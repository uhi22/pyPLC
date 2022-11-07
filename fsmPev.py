# State machine for the car
#
#

#------------------------------------------------------------

import pyPlcTcpSocket
import time # for time.sleep()
from exiConnector import * # for EXI data handling/converting

stateInitialized = 0
stateWaitForSupportedApplicationProtocolResponse = 1
stateWaitForSessionSetupResponse = 2
stateWaitForServiceDiscoveryResponse = 3
stateWaitForPaymentServiceSelectionResponse = 4
stateWaitForAuthorizationResponse = 5
stateWaitForChargeParameterResponse = 6
stateWaitForCableCheckResponse = 7
stateWaitForPreChargeResponse = 8
stateWaitForPowerDeliveryResponse = 9

class fsmPev():
    def enterState(self, n):
        print("from " + str(self.state) + " entering " + str(n))
        self.state = n
        self.cyclesInState = 0
        
    def isTooLong(self):
        # The timeout handling function.
        return (self.cyclesInState > 20)
        
    def stateFunctionInitialized(self):
        if (self.Tcp.isConnected):
            # self.Tcp.transmit(bytes("TestFromPevInInitialized", "utf-8"))
            self.Tcp.transmit(addV2GTPHeader(exiHexToByteArray(exiHexDemoSupportedApplicationProtocolRequestIoniq)))
            self.enterState(stateWaitForSupportedApplicationProtocolResponse)
        
    def stateFunctionWaitForSupportedApplicationProtocolResponse(self):
        if (len(self.rxData)>0):
            pass
       
    stateFunctions = { 
            stateInitialized: stateFunctionInitialized,
            stateWaitForSupportedApplicationProtocolResponse: stateFunctionWaitForSupportedApplicationProtocolResponse,
        }

    def reInit(self):
        print("re-initializing fsmPev") 
        self.state = stateInitialized
        self.cyclesInState = 0
        self.rxData = []
        if (not self.Tcp.isConnected):
            self.Tcp.connect('fe80::e0ad:99ac:52eb:85d3', 15118)
            if (not self.Tcp.isConnected):
                print("connection failed")
            else:
                print("connected")
        
    def __init__(self):
        print("initializing fsmPev") 
        self.Tcp = pyPlcTcpSocket.pyPlcTcpClientSocket()
        self.reInit()
                
    def mainfunction(self):
        #self.Tcp.mainfunction() # call the lower-level worker
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
    print("Testing the pev state machine")
    pev = fsmPev()
    print("Press Ctrl-Break for aborting")
    while (True):
        time.sleep(0.1)
        pev.mainfunction()
        

