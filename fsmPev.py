# State machine for the car
#
#

#------------------------------------------------------------

import pyPlcTcpSocket
import time # for time.sleep()
from helpers import prettyHexMessage
from exiConnector import * # for EXI data handling/converting
import json

stateInitialized = 0
stateWaitForSupportedApplicationProtocolResponse = 1
stateWaitForSessionSetupResponse = 2
stateWaitForServiceDiscoveryResponse = 3
stateWaitForServicePaymentSelectionResponse = 4
stateWaitForAuthorizationResponse = 5
stateWaitForChargeParameterDiscoveryResponse = 6
stateWaitForCableCheckResponse = 7
stateWaitForPreChargeResponse = 8
stateWaitForPowerDeliveryResponse = 9
stateNotYetInitialized = 10

dinEVSEProcessingType_Finished = "0"
dinEVSEProcessingType_Ongoing = "1"

class fsmPev():
    def addToTrace(self, s):
        self.callbackAddToTrace(s)
        
    def enterState(self, n):
        print("from " + str(self.state) + " entering " + str(n))
        self.state = n
        self.cyclesInState = 0
        
    def isTooLong(self):
        # The timeout handling function.
        limit = 30 # number of call cycles until timeout
        if (self.state==stateWaitForCableCheckResponse):
            limit = 30*30 # CableCheck may need some time. Wait at least 30s.
        if (self.state==stateWaitForPreChargeResponse):
            limit = 30*30 # PreCharge may need some time. Wait at least 30s.
        return (self.cyclesInState > limit)
        
    def stateFunctionInitialized(self):
        if (self.Tcp.isConnected):
            # we just use the initial request message from the Ioniq. It contains one entry: DIN.
            self.Tcp.transmit(addV2GTPHeader(exiHexToByteArray(exiHexDemoSupportedApplicationProtocolRequestIoniq)))
            self.enterState(stateWaitForSupportedApplicationProtocolResponse)
        
    def stateFunctionWaitForSupportedApplicationProtocolResponse(self):
        if (len(self.rxData)>0):
            self.addToTrace("In state WaitForSupportedApplicationProtocolResponse, received " + prettyHexMessage(self.rxData))
            exidata = removeV2GTPHeader(self.rxData)
            self.rxData = []
            strConverterResult = exiDecode(exidata, "Dh") # Decode Handshake-response
            self.addToTrace(strConverterResult)
            if (strConverterResult.find("supportedAppProtocolRes")>0):
                # todo: check the request content, and fill response parameters
                msg = addV2GTPHeader(exiEncode("EDA")) # EDA for Encode, Din, SessionSetupReq
                self.addToTrace("responding " + prettyHexMessage(msg))
                self.Tcp.transmit(msg)
                self.enterState(stateWaitForSessionSetupResponse)
        if (self.isTooLong()):
            self.enterState(0)
            
    def stateFunctionWaitForSessionSetupResponse(self):
        if (len(self.rxData)>0):
            self.addToTrace("In state WaitForSessionSetupResponse, received " + prettyHexMessage(self.rxData))
            exidata = removeV2GTPHeader(self.rxData)
            self.rxData = []
            strConverterResult = exiDecode(exidata, "DD") # Decode DIN
            self.addToTrace(strConverterResult)
            if (strConverterResult.find("SessionSetupRes")>0):
                # todo: check the request content, and fill response parameters
                try:
                    y = json.loads(strConverterResult)
                    strSessionId = y["header.SessionID"]
                    self.addToTrace("[PEV] The Evse decided for SessionId " + strSessionId)
                    self.sessionId = strSessionId
                except:
                    self.addToTrace("ERROR: Could not decode the sessionID")
                msg = addV2GTPHeader(exiEncode("EDB_"+self.sessionId)) # EDB for Encode, Din, ServiceDiscoveryRequest
                self.addToTrace("responding " + prettyHexMessage(msg))
                self.Tcp.transmit(msg)
                self.enterState(stateWaitForServiceDiscoveryResponse)
        if (self.isTooLong()):
            self.enterState(0)

    def stateFunctionWaitForServiceDiscoveryResponse(self):
        if (len(self.rxData)>0):
            self.addToTrace("In state WaitForServiceDiscoveryResponse, received " + prettyHexMessage(self.rxData))
            exidata = removeV2GTPHeader(self.rxData)
            self.rxData = []
            strConverterResult = exiDecode(exidata, "DD") # Decode DIN
            self.addToTrace(strConverterResult)
            if (strConverterResult.find("ServiceDiscoveryRes")>0):
                # todo: check the request content, and fill response parameters
                msg = addV2GTPHeader(exiEncode("EDC_"+self.sessionId)) # EDC for Encode, Din, ServicePaymentSelection
                self.addToTrace("responding " + prettyHexMessage(msg))
                self.Tcp.transmit(msg)
                self.enterState(stateWaitForServicePaymentSelectionResponse)
        if (self.isTooLong()):
            self.enterState(0)

    def stateFunctionWaitForServicePaymentSelectionResponse(self):
        if (len(self.rxData)>0):
            self.addToTrace("In state WaitForServicePaymentSelectionResponse, received " + prettyHexMessage(self.rxData))
            exidata = removeV2GTPHeader(self.rxData)
            self.rxData = []
            strConverterResult = exiDecode(exidata, "DD") # Decode DIN
            self.addToTrace(strConverterResult)
            if (strConverterResult.find("ServicePaymentSelectionRes")>0):
                # todo: check the request content, and fill response parameters
                msg = addV2GTPHeader(exiEncode("EDE_"+self.sessionId)) # EDE for Encode, Din, ChargeParameterDiscovery. We ignore Authorization, not specified in DIN.
                self.addToTrace("responding " + prettyHexMessage(msg))
                self.Tcp.transmit(msg)
                self.enterState(stateWaitForChargeParameterDiscoveryResponse)
        if (self.isTooLong()):
            self.enterState(0)
        
    def stateFunctionWaitForChargeParameterDiscoveryResponse(self):
        if (len(self.rxData)>0):
            self.addToTrace("In state WaitForChargeParameterDiscoveryResponse, received " + prettyHexMessage(self.rxData))
            exidata = removeV2GTPHeader(self.rxData)
            self.rxData = []
            strConverterResult = exiDecode(exidata, "DD") # Decode DIN
            self.addToTrace(strConverterResult)
            if (strConverterResult.find("ChargeParameterDiscoveryRes")>0):
                # todo: check the request content, and fill response parameters
                msg = addV2GTPHeader(exiEncode("EDF_"+self.sessionId)) # EDF for Encode, Din, CableCheck
                self.addToTrace("responding " + prettyHexMessage(msg))
                self.Tcp.transmit(msg)
                self.enterState(stateWaitForCableCheckResponse)
        if (self.isTooLong()):
            self.enterState(0)

    def stateFunctionWaitForCableCheckResponse(self):
        if (len(self.rxData)>0):
            self.addToTrace("In state WaitForCableCheckResponse, received " + prettyHexMessage(self.rxData))
            exidata = removeV2GTPHeader(self.rxData)
            self.rxData = []
            strConverterResult = exiDecode(exidata, "DD") # Decode DIN
            self.addToTrace(strConverterResult)
            if (strConverterResult.find("CableCheckRes")>0):
                try:
                    y = json.loads(strConverterResult)
                    strResponseCode = y["ResponseCode"]
                    strEVSEProcessing = y["EVSEProcessing"]
                    self.addToTrace("[PEV] The CableCheck result is " + strResponseCode + " " + strEVSEProcessing)
                except:
                    self.addToTrace("ERROR: Could not decode the CableCheckRes")
                # todo: check the request content, and fill response parameters
                # We have two cases here:
                # 1) The charger says "cable check is finished and cable ok", by setting ResponseCode=OK and EVSEProcessing=Finished.
                # 2) Else: The charger says "need more time or cable not ok". In this case, we just run into timeout and start from the beginning.
                if ((strEVSEProcessing==dinEVSEProcessingType_Finished) and (strResponseCode=="OK")):
                    msg = addV2GTPHeader(exiEncode("EDG_"+self.sessionId)) # EDG for Encode, Din, PreCharge
                    self.addToTrace("responding " + prettyHexMessage(msg))
                    self.Tcp.transmit(msg)
                    self.enterState(stateWaitForPreChargeResponse)
                else:
                    # cable check not yet finished or finished with bad result -> try again
                    msg = addV2GTPHeader(exiEncode("EDF_"+self.sessionId)) # EDF for Encode, Din, CableCheck
                    self.addToTrace("responding " + prettyHexMessage(msg))
                    self.Tcp.transmit(msg)
                    
        if (self.isTooLong()):
            self.enterState(0)

    def stateFunctionWaitForPreChargeResponse(self):
        if (self.DelayCycles>0):
            self.DelayCycles-=1
            return    
        if (len(self.rxData)>0):
            self.addToTrace("In state WaitForPreChargeResponse, received " + prettyHexMessage(self.rxData))
            exidata = removeV2GTPHeader(self.rxData)
            self.rxData = []
            strConverterResult = exiDecode(exidata, "DD") # Decode DIN
            self.addToTrace(strConverterResult)
            if (strConverterResult.find("PreChargeRes")>0):
                # todo: check the request content, and fill response parameters
                self.addToTrace("PreCharge aknowledge received.")
                self.addToTrace("As Demo, we stay in PreCharge forever.")
                msg = addV2GTPHeader(exiEncode("EDG_"+self.sessionId)) # EDG for Encode, Din, PreCharge
                self.addToTrace("responding " + prettyHexMessage(msg))
                self.Tcp.transmit(msg)
                self.DelayCycles=15 # wait with the next evaluation approx half a second
        if (self.isTooLong()):
            self.enterState(0)
    
    def stateFunctionNotYetInitialized(self):
        pass # nothing to do, just wait for external event for re-initialization
        
    stateFunctions = { 
            stateInitialized: stateFunctionInitialized,
            stateWaitForSupportedApplicationProtocolResponse: stateFunctionWaitForSupportedApplicationProtocolResponse,
            stateWaitForSessionSetupResponse: stateFunctionWaitForSessionSetupResponse,
            stateWaitForServiceDiscoveryResponse: stateFunctionWaitForServiceDiscoveryResponse,
            stateWaitForServicePaymentSelectionResponse: stateFunctionWaitForServicePaymentSelectionResponse,
            stateWaitForChargeParameterDiscoveryResponse: stateFunctionWaitForChargeParameterDiscoveryResponse,
            stateWaitForCableCheckResponse: stateFunctionWaitForCableCheckResponse,
            stateWaitForPreChargeResponse: stateFunctionWaitForPreChargeResponse,
            stateNotYetInitialized: stateFunctionNotYetInitialized
        }

    def reInit(self):
        self.addToTrace("re-initializing fsmPev") 
        self.state = stateInitialized
        self.cyclesInState = 0
        self.rxData = []
        if (not self.Tcp.isConnected):
            #evseIp = 'fe80:0000:0000:0000:c690:83f3:fbcb:980e'
            evseIp = self.addressManager.getSeccIp() # the EVSE IP address which was found out with SDP
            self.Tcp.connect(evseIp, 15118)
            if (not self.Tcp.isConnected):
                self.addToTrace("connection failed")
            else:
                self.addToTrace("connected")
        
    def __init__(self, addressManager, callbackAddToTrace):
        self.callbackAddToTrace = callbackAddToTrace
        self.addToTrace("initializing fsmPev") 
        self.Tcp = pyPlcTcpSocket.pyPlcTcpClientSocket(self.callbackAddToTrace)
        self.addressManager = addressManager
        self.state = stateNotYetInitialized
        self.sessionId = "DEAD55AADEAD55AA"
        self.cyclesInState = 0
        self.DelayCycles = 0
        self.rxData = []        
        # we do NOT call the reInit, because we want to wait with the connection until external trigger comes
                
    def mainfunction(self):
        #self.Tcp.mainfunction() # call the lower-level worker
        if (self.Tcp.isRxDataAvailable()):
                self.rxData = self.Tcp.getRxData()
                #self.addToTrace("received " + prettyHexMessage(self.rxData))
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
        

