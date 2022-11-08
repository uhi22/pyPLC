# State machine for the charger
#
#

#------------------------------------------------------------

import pyPlcTcpSocket
import time # for time.sleep()
from helpers import prettyHexMessage
from exiConnector import * # for EXI data handling/converting

stateWaitForSupportedApplicationProtocolRequest = 0
stateWaitForSessionSetupRequest = 1
stateWaitForServiceDiscoveryRequest = 2
stateWaitForServicePaymentSelectionRequest = 3
stateWaitForAuthorizationRequest = 4
stateWaitForChargeParameterDiscoveryRequest = 5
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
        return (self.cyclesInState > 50)
        
        
    def stateFunctionWaitForSupportedApplicationProtocolRequest(self):
        if (len(self.rxData)>0):
            print("In state WaitForSupportedApplicationProtocolRequest, received " + prettyHexMessage(self.rxData))
            exidata = removeV2GTPHeader(self.rxData)
            self.rxData = []
            strConverterResult = exiDecode(exidata, "DH") # Decode Handshake-request
            print(strConverterResult)
            if (strConverterResult.find("ProtocolNamespace=urn:din")>0):
                # todo: of course we should care for schemaID and prio also here
                print("Detected DIN")
                # Eh for encode handshake, SupportedApplicationProtocolResponse
                msg = addV2GTPHeader(exiEncode("Eh"))
                print("responding " + prettyHexMessage(msg))
                self.Tcp.transmit(msg)
                self.enterState(stateWaitForSessionSetupRequest)
        
    def stateFunctionWaitForSessionSetupRequest(self):
        if (len(self.rxData)>0):
            print("In state stateFunctionWaitForSessionSetupRequest, received " + prettyHexMessage(self.rxData))
            exidata = removeV2GTPHeader(self.rxData)
            self.rxData = []
            strConverterResult = exiDecode(exidata, "DD")
            print(strConverterResult)
            if (strConverterResult.find("SessionSetupReq")>0):
                # todo: check the request content, and fill response parameters
                msg = addV2GTPHeader(exiEncode("EDa")) # EDa for Encode, Din, SessionSetupResponse
                print("responding " + prettyHexMessage(msg))
                self.Tcp.transmit(msg)  
                self.enterState(stateWaitForServiceDiscoveryRequest)
        if (self.isTooLong()):
            self.enterState(0)
            
    def stateFunctionWaitForServiceDiscoveryRequest(self):
        if (len(self.rxData)>0):
            print("In state WaitForServiceDiscoveryRequest, received " + prettyHexMessage(self.rxData))
            exidata = removeV2GTPHeader(self.rxData)
            self.rxData = []
            strConverterResult = exiDecode(exidata, "DD")
            print(strConverterResult)
            if (strConverterResult.find("ServiceDiscoveryReq")>0):
                # todo: check the request content, and fill response parameters
                msg = addV2GTPHeader(exiEncode("EDb")) # EDb for Encode, Din, ServiceDiscoveryResponse
                print("responding " + prettyHexMessage(msg))
                self.Tcp.transmit(msg)  
                self.enterState(stateWaitForServicePaymentSelectionRequest)
        if (self.isTooLong()):
            self.enterState(0)
            
    def stateFunctionWaitForServicePaymentSelectionRequest(self):
        if (len(self.rxData)>0):
            print("In state WaitForServicePaymentSelectionRequest, received " + prettyHexMessage(self.rxData))
            exidata = removeV2GTPHeader(self.rxData)
            self.rxData = []
            strConverterResult = exiDecode(exidata, "DD")
            print(strConverterResult)
            if (strConverterResult.find("ServicePaymentSelectionReq")>0):
                # todo: check the request content, and fill response parameters
                msg = addV2GTPHeader(exiEncode("EDc")) # EDc for Encode, Din, ServicePaymentSelectionResponse
                print("responding " + prettyHexMessage(msg))
                self.Tcp.transmit(msg)  
                self.enterState(stateWaitForChargeParameterDiscoveryRequest)
        if (self.isTooLong()):
            self.enterState(0)
            
    def stateFunctionWaitForAuthorizationRequest(self): # not specified in the DIN
        if (len(self.rxData)>0):
            self.rxData = []
            self.enterState(5)
        if (self.isTooLong()):
            self.enterState(0)
            
    def stateFunctionWaitForChargeParameterDiscoveryRequest(self):
        if (len(self.rxData)>0):
            print("In state WaitForChargeParameterDiscoveryRequest, received " + prettyHexMessage(self.rxData))
            exidata = removeV2GTPHeader(self.rxData)
            self.rxData = []
            strConverterResult = exiDecode(exidata, "DD")
            print(strConverterResult)
            if (strConverterResult.find("ChargeParameterDiscoveryReq")>0):
                # todo: check the request content, and fill response parameters
                msg = addV2GTPHeader(exiEncode("EDe")) # EDe for Encode, Din, ChargeParameterDiscoveryResponse
                print("responding " + prettyHexMessage(msg))
                self.Tcp.transmit(msg)
                self.enterState(stateWaitForCableCheckRequest)
        if (self.isTooLong()):
            self.enterState(0)
            
    def stateFunctionWaitForCableCheckRequest(self):
        if (len(self.rxData)>0):
            print("In state WaitForCableCheckRequest, received " + prettyHexMessage(self.rxData))
            exidata = removeV2GTPHeader(self.rxData)
            self.rxData = []
            strConverterResult = exiDecode(exidata, "DD")
            print(strConverterResult)
            if (strConverterResult.find("CableCheckReq")>0):
                # todo: check the request content, and fill response parameters
                msg = addV2GTPHeader(exiEncode("EDf")) # EDf for Encode, Din, CableCheckResponse
                print("responding " + prettyHexMessage(msg))
                self.Tcp.transmit(msg)
                self.enterState(stateWaitForPreChargeRequest)
        if (self.isTooLong()):
            self.enterState(0)
            
    def stateFunctionWaitForPreChargeRequest(self):
        if (len(self.rxData)>0):
            print("In state WaitForPreChargeRequest, received " + prettyHexMessage(self.rxData))
            exidata = removeV2GTPHeader(self.rxData)
            self.rxData = []
            strConverterResult = exiDecode(exidata, "DD")
            print(strConverterResult)
            if (strConverterResult.find("PreChargeReq")>0):
                # todo: check the request content, and fill response parameters
                msg = addV2GTPHeader(exiEncode("EDg")) # EDf for Encode, Din, PreChargeResponse
                print("responding " + prettyHexMessage(msg))
                self.Tcp.transmit(msg)
                self.enterState(stateWaitForPowerDeliveryRequest)
        if (self.isTooLong()):
            self.enterState(0)
            
    def stateFunctionWaitForPowerDeliveryRequest(self):
        if (len(self.rxData)>0):
            print("In state WaitForPowerDeliveryRequest, received " + prettyHexMessage(self.rxData))
            print("Todo: Reaction in state WaitForPowerDeliveryRequest is not implemented yet.")
            self.rxData = []
            self.enterState(0)
        if (self.isTooLong()):
            self.enterState(0)
            
       
    stateFunctions = { 
            stateWaitForSupportedApplicationProtocolRequest: stateFunctionWaitForSupportedApplicationProtocolRequest,
            stateWaitForSessionSetupRequest: stateFunctionWaitForSessionSetupRequest,
            stateWaitForServiceDiscoveryRequest: stateFunctionWaitForServiceDiscoveryRequest,
            stateWaitForServicePaymentSelectionRequest: stateFunctionWaitForServicePaymentSelectionRequest,
            # stateWaitForAuthorizationRequest: stateFunctionWaitForAuthorizationRequest, not in DIN
            stateWaitForChargeParameterDiscoveryRequest: stateFunctionWaitForChargeParameterDiscoveryRequest,
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
                #print("received " + str(self.rxData))
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
        

