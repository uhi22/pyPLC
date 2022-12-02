# State machine for the car
#
#

#------------------------------------------------------------

import pyPlcTcpSocket
import time # for time.sleep()
from helpers import prettyHexMessage
from exiConnector import * # for EXI data handling/converting
import json

stateNotYetInitialized = 0
stateConnecting = 1
stateConnected = 2
stateWaitForSupportedApplicationProtocolResponse = 3
stateWaitForSessionSetupResponse = 4
stateWaitForServiceDiscoveryResponse = 5
stateWaitForServicePaymentSelectionResponse = 6
stateWaitForContractAuthenticationResponse = 7
stateWaitForChargeParameterDiscoveryResponse = 8
stateWaitForCableCheckResponse = 9
stateWaitForPreChargeResponse = 10
stateWaitForPowerDeliveryResponse = 11
stateSequenceTimeout = 99


dinEVSEProcessingType_Finished = "0"
dinEVSEProcessingType_Ongoing = "1"

class fsmPev():
    def addToTrace(self, s):
        self.callbackAddToTrace("[PEV] " + s)
        
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
        
    def stateFunctionNotYetInitialized(self):
        pass # nothing to do, just wait for external event for re-initialization

    def stateFunctionConnecting(self):
        if (self.cyclesInState<30): # The first second in the state just do nothing.
            return
        evseIp = self.addressManager.getSeccIp() # the chargers IP address which was announced in SDP
        seccTcpPort = self.addressManager.getSeccTcpPort() # the chargers TCP port which was announced in SDP
        self.Tcp.connect(evseIp, seccTcpPort) # This is a blocking call. If we come back, we are connected, or not.
        if (not self.Tcp.isConnected):
            # Bad case: Connection did not work. May happen if we are too fast and the charger needs more
            # time until the socket is ready. Or the charger is defective. Or somebody pulled the plug.
            # No matter what is the reason, we just try again and again. What else would make sense?
            self.addToTrace("Connection failed. Will try again.")
            self.reInit() # stay in same state, reset the cyclesInState and try again
            return
        else:
            # Good case: We are connected. Change to the next state.
            self.addToTrace("connected")
            self.enterState(stateConnected)
            return
    
    def stateFunctionConnected(self):
        # We have a freshly established TCP channel. We start the V2GTP/EXI communication now.
        # We just use the initial request message from the Ioniq. It contains one entry: DIN.
        self.addToTrace("Sending the initial SupportedApplicationProtocolReq")
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
                self.addToTrace("Will send SessionSetupReq")
                msg = addV2GTPHeader(exiEncode("EDA")) # EDA for Encode, Din, SessionSetupReq
                self.addToTrace("responding " + prettyHexMessage(msg))
                self.Tcp.transmit(msg)
                self.enterState(stateWaitForSessionSetupResponse)
        if (self.isTooLong()):
            self.enterState(stateSequenceTimeout)
            
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
                    self.addToTrace("The Evse decided for SessionId " + strSessionId)
                    self.sessionId = strSessionId
                except:
                    self.addToTrace("ERROR: Could not decode the sessionID")
                self.addToTrace("Will send ServiceDiscoveryReq")
                msg = addV2GTPHeader(exiEncode("EDB_"+self.sessionId)) # EDB for Encode, Din, ServiceDiscoveryRequest
                self.addToTrace("responding " + prettyHexMessage(msg))
                self.Tcp.transmit(msg)
                self.enterState(stateWaitForServiceDiscoveryResponse)
        if (self.isTooLong()):
            self.enterState(stateSequenceTimeout)

    def stateFunctionWaitForServiceDiscoveryResponse(self):
        if (len(self.rxData)>0):
            self.addToTrace("In state WaitForServiceDiscoveryResponse, received " + prettyHexMessage(self.rxData))
            exidata = removeV2GTPHeader(self.rxData)
            self.rxData = []
            strConverterResult = exiDecode(exidata, "DD") # Decode DIN
            self.addToTrace(strConverterResult)
            if (strConverterResult.find("ServiceDiscoveryRes")>0):
                # todo: check the request content, and fill response parameters
                self.addToTrace("Will send ServicePaymentSelectionReq")
                msg = addV2GTPHeader(exiEncode("EDC_"+self.sessionId)) # EDC for Encode, Din, ServicePaymentSelection
                self.addToTrace("responding " + prettyHexMessage(msg))
                self.Tcp.transmit(msg)
                self.enterState(stateWaitForServicePaymentSelectionResponse)
        if (self.isTooLong()):
            self.enterState(stateSequenceTimeout)

    def stateFunctionWaitForServicePaymentSelectionResponse(self):
        if (len(self.rxData)>0):
            self.addToTrace("In state WaitForServicePaymentSelectionResponse, received " + prettyHexMessage(self.rxData))
            exidata = removeV2GTPHeader(self.rxData)
            self.rxData = []
            strConverterResult = exiDecode(exidata, "DD") # Decode DIN
            self.addToTrace(strConverterResult)
            if (strConverterResult.find("ServicePaymentSelectionRes")>0):
                # todo: check the request content, and fill response parameters
                self.addToTrace("Will send ContractAuthenticationReq")
                msg = addV2GTPHeader(exiEncode("EDL_"+self.sessionId)) # EDL for Encode, Din, ContractAuthenticationReq.
                self.addToTrace("responding " + prettyHexMessage(msg))
                self.Tcp.transmit(msg)
                self.numberOfContractAuthenticationReq = 1 # This is the first request.
                self.enterState(stateWaitForContractAuthenticationResponse)
        if (self.isTooLong()):
            self.enterState(stateSequenceTimeout)
                
    def stateFunctionWaitForContractAuthenticationResponse(self):
        if (self.cyclesInState<30): # The first second in the state just do nothing.
            return
        if (len(self.rxData)>0):
            self.addToTrace("In state WaitForContractAuthentication, received " + prettyHexMessage(self.rxData))
            exidata = removeV2GTPHeader(self.rxData)
            self.rxData = []
            strConverterResult = exiDecode(exidata, "DD") # Decode DIN
            self.addToTrace(strConverterResult)
            if (strConverterResult.find("ContractAuthenticationRes")>0):
                # In normal case, we can have two results here: either the Authentication is needed (the user
                # needs to authorize by RFID card or app, or something like this.
                # Or, the authorization is finished. This is shown by EVSEProcessing=Finished.
                if (strConverterResult.find('"EVSEProcessing": "Finished"')>0):                
                    self.addToTrace("It is Finished. Will send ChargeParameterDiscoveryReq")
                    msg = addV2GTPHeader(exiEncode("EDE_"+self.sessionId)) # EDE for Encode, Din, ChargeParameterDiscovery.
                    self.addToTrace("responding " + prettyHexMessage(msg))
                    self.Tcp.transmit(msg)
                    self.enterState(stateWaitForChargeParameterDiscoveryResponse)
                else:
                    # Not (yet) finished.
                    if (self.numberOfContractAuthenticationReq>=120): # approx 120 seconds, maybe the user searches two minutes for his RFID card...
                        self.addToTrace("Authentication lasted too long. " + str(self.numberOfContractAuthenticationReq) + " Giving up.")
                        self.enterState(stateSequenceTimeout)
                    else:
                         # Try again.
                        self.numberOfContractAuthenticationReq += 1 # count the number of tries.
                        self.addToTrace("Not (yet) finished. Will again send ContractAuthenticationReq #" + str(self.numberOfContractAuthenticationReq))
                        msg = addV2GTPHeader(exiEncode("EDL_"+self.sessionId)) # EDL for Encode, Din, ContractAuthenticationReq.
                        self.addToTrace("responding " + prettyHexMessage(msg))
                        self.Tcp.transmit(msg)
                        # We just stay in the same state, until the timeout elapses.
                        self.enterState(stateWaitForContractAuthenticationResponse) 
        if (self.isTooLong()):
            # The timeout in case if nothing is received at all.
            self.enterState(stateSequenceTimeout)
        
    def stateFunctionWaitForChargeParameterDiscoveryResponse(self):
        if (len(self.rxData)>0):
            self.addToTrace("In state WaitForChargeParameterDiscoveryResponse, received " + prettyHexMessage(self.rxData))
            exidata = removeV2GTPHeader(self.rxData)
            self.rxData = []
            strConverterResult = exiDecode(exidata, "DD") # Decode DIN
            self.addToTrace(strConverterResult)
            if (strConverterResult.find("ChargeParameterDiscoveryRes")>0):
                # todo: check the request content, and fill response parameters
                # todo: if the response is "OK", pull the CP line to state C here.
                # self.hardwareInterface.changeToStateC()
                self.addToTrace("Will send CableCheckReq")
                msg = addV2GTPHeader(exiEncode("EDF_"+self.sessionId)) # EDF for Encode, Din, CableCheck
                self.addToTrace("responding " + prettyHexMessage(msg))
                self.Tcp.transmit(msg)
                self.enterState(stateWaitForCableCheckResponse)
        if (self.isTooLong()):
            self.enterState(stateSequenceTimeout)

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
                    self.addToTrace("The EVSE says that the CableCheck is finished and ok.")
                    self.addToTrace("Will send PreChargeReq")
                    msg = addV2GTPHeader(exiEncode("EDG_"+self.sessionId)) # EDG for Encode, Din, PreCharge
                    self.addToTrace("responding " + prettyHexMessage(msg))
                    self.Tcp.transmit(msg)
                    self.enterState(stateWaitForPreChargeResponse)
                else:
                    # cable check not yet finished or finished with bad result -> try again
                    self.addToTrace("Will again send CableCheckReq")
                    msg = addV2GTPHeader(exiEncode("EDF_"+self.sessionId)) # EDF for Encode, Din, CableCheck
                    self.addToTrace("responding " + prettyHexMessage(msg))
                    self.Tcp.transmit(msg)
                    
        if (self.isTooLong()):
            self.enterState(stateSequenceTimeout)

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
            self.enterState(stateSequenceTimeout)
            
    def stateFunctionSequenceTimeout(self):
        # Here we end, if we run into a timeout in the state machine. This is an error case, and
        # we should re-initalize and try again to get a communication.
        # Todo: Maybe we want even inform the pyPlcHomeplug to do a new SLAC.
        # For the moment, we just re-establish the TCP connection.
        self.reInit()
    
        
    stateFunctions = { 
            stateNotYetInitialized: stateFunctionNotYetInitialized,
            stateConnecting: stateFunctionConnecting,
            stateConnected: stateFunctionConnected,
            stateWaitForSupportedApplicationProtocolResponse: stateFunctionWaitForSupportedApplicationProtocolResponse,
            stateWaitForSessionSetupResponse: stateFunctionWaitForSessionSetupResponse,
            stateWaitForServiceDiscoveryResponse: stateFunctionWaitForServiceDiscoveryResponse,
            stateWaitForServicePaymentSelectionResponse: stateFunctionWaitForServicePaymentSelectionResponse,
            stateWaitForContractAuthenticationResponse: stateFunctionWaitForContractAuthenticationResponse,
            stateWaitForChargeParameterDiscoveryResponse: stateFunctionWaitForChargeParameterDiscoveryResponse,
            stateWaitForCableCheckResponse: stateFunctionWaitForCableCheckResponse,
            stateWaitForPreChargeResponse: stateFunctionWaitForPreChargeResponse,
            stateSequenceTimeout: stateFunctionSequenceTimeout
        }

    def reInit(self):
        self.addToTrace("re-initializing fsmPev") 
        self.Tcp.disconnect()
        self.state = stateConnecting
        self.cyclesInState = 0
        self.rxData = []
        
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
        

