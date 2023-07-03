# State machine for the car
#
#

#------------------------------------------------------------

import pyPlcTcpSocket
import time # for time.sleep()
from datetime import datetime
from helpers import prettyHexMessage, compactHexMessage, combineValueAndMultiplier
from mytestsuite import *
from exiConnector import * # for EXI data handling/converting
import json
from configmodule import getConfigValue, getConfigValueBool


stateNotYetInitialized = 0
stateConnecting = 1
stateConnected = 2
stateWaitForSupportedApplicationProtocolResponse = 3
stateWaitForSessionSetupResponse = 4
stateWaitForServiceDiscoveryResponse = 5
stateWaitForServicePaymentSelectionResponse = 6
stateWaitForContractAuthenticationResponse = 7
stateWaitForChargeParameterDiscoveryResponse = 8
stateWaitForConnectorLock = 9
stateWaitForCableCheckResponse = 10
stateWaitForPreChargeResponse = 11
stateWaitForContactorsClosed = 12
stateWaitForPowerDeliveryResponse = 13
stateWaitForCurrentDemandResponse = 14
stateWaitForWeldingDetectionResponse = 15
stateWaitForSessionStopResponse = 16
stateChargingFinished = 17
stateUnrecoverableError = 88
stateSequenceTimeout = 99
stateSafeShutDownWaitForChargerShutdown = 111
stateSafeShutDownWaitForContactorsOpen = 222
stateEnd = 1000



dinEVSEProcessingType_Finished = "0"
dinEVSEProcessingType_Ongoing = "1"

class fsmPev():
    def addToTrace(self, s):
        self.callbackAddToTrace("[PEV] " + s)
        
    def publishStatus(self, s, strAuxInfo1="", strAuxInfo2=""):
        self.callbackShowStatus(s, "pevState", strAuxInfo1, strAuxInfo2)
        
    def exiDecode(self, exidata, schema):
        self.connMgr.ApplOk()
        s = compactHexMessage(exidata)
        strDateTime=datetime.today().strftime('%Y-%m-%dT%H:%M:%S.%f')
        self.exiLogFile.write(strDateTime + "=" + schema + " " + s +"\n") # write the EXI data to the exiLogFile
        return exiDecode(exidata, schema) # call the decoder
        
    def exiEncode(self, input):
        schema = input[0:2]
        exidata = exiEncode(input) # call the encoder
        s = exidata # it is already a hex string
        strDateTime=datetime.today().strftime('%Y-%m-%dT%H:%M:%S.%f')
        self.exiLogFile.write(strDateTime + "=" + schema + " " + s +"\n") # write the EXI data to the exiLogFile
        return exidata
        
    def prettifyState(self, statenumber):
        s="unknownState"
        if (statenumber == stateNotYetInitialized):
            s = "NotYetInitialized"
        if (statenumber == stateConnecting):
            s = "Connecting"
        if (statenumber == stateConnected):
            s = "Connected"
        if (statenumber == stateWaitForSupportedApplicationProtocolResponse):
            s = "WaitForSupportedApplicationProtocolResponse"
        if (statenumber == stateWaitForSessionSetupResponse):
            s = "WaitForSessionSetupResponse"
        if (statenumber == stateWaitForServiceDiscoveryResponse):
            s = "WaitForServiceDiscoveryResponse"
        if (statenumber == stateWaitForServicePaymentSelectionResponse):
            s = "WaitForServicePaymentSelectionResponse"
        if (statenumber == stateWaitForContractAuthenticationResponse):
            s = "WaitForContractAuthenticationResponse"
        if (statenumber == stateWaitForChargeParameterDiscoveryResponse):
            s = "WaitForChargeParameterDiscoveryResponse"
        if (statenumber == stateWaitForConnectorLock):
            s = "WaitForConnectorLock"
        if (statenumber == stateWaitForCableCheckResponse):
            s = "WaitForCableCheckResponse"
        if (statenumber == stateWaitForPreChargeResponse):
            s = "WaitForPreChargeResponse"
        if (statenumber == stateWaitForContactorsClosed):
            s = "WaitForContactorsClosed"
        if (statenumber == stateWaitForPowerDeliveryResponse):
            s = "WaitForPowerDeliveryResponse"
        if (statenumber == stateWaitForCurrentDemandResponse):
            s = "WaitForCurrentDemandResponse"
        if (statenumber == stateWaitForWeldingDetectionResponse):
            s = "WaitForWeldingDetectionResponse"
        if (statenumber == stateWaitForSessionStopResponse):
            s = "WaitForSessionStopResponse"
        if (statenumber == stateChargingFinished):
            s = "ChargingFinished"
        if (statenumber == stateUnrecoverableError):
            s = "UnrecoverableError"
        if (statenumber == stateSequenceTimeout):
            s = "SequenceTimeout"
        if (statenumber == stateSafeShutDownWaitForChargerShutdown):
            s = "SafeShutDownWaitForChargerShutdown"
        if (statenumber == stateSafeShutDownWaitForContactorsOpen):
            s = "SafeShutDownWaitForContactorsOpen"
        if (statenumber == stateEnd):
            s = "End"
        return s
    
    def  isErrorEvseStatusCode(self, strEvseStatusCode):
        # 0 is EVSE_NotReady. This may be normal, no error, just wait.
        # 1 is EVSE_Ready: The normal case.
        if (strEvseStatusCode == "2"): # EVSE_Shutdown: The user stopped the charging normally on charger.
            self.addToTrace("EVSE_Shutdown. Seems the user canceled the charging on the charger.")
            self.publishStatus("EVSE_Shutdown")
            return True
        if (strEvseStatusCode == "3"): # EVSE_UtilityInterruptEvent: Stopped or power reduction
            self.addToTrace("EVSE_UtilityInterruptEvent.")
            self.publishStatus("EVSE_UtilityInterruptEvent")
            return True
        # 4 is EVSE_IsolationMonitoringActive. This is normal, no error.
        if (strEvseStatusCode == "5"): # EVSE_EmergencyShutdown: Error or Notaus button
            self.addToTrace("EVSE_EmergencyShutdown.")
            self.publishStatus("EVSE_EmergencyShutdown")
            return True
        if (strEvseStatusCode == "6"): # EVSE_Malfunction: Error
            self.addToTrace("EVSE_Malfunction.")
            self.publishStatus("EVSE_Malfunction")
            return True
        if (strEvseStatusCode == "7"): # Reserved, Error
            return True
        if (strEvseStatusCode == "8"): # Reserved, Error
            return True
        if (strEvseStatusCode == "9"): # Reserved, Error
            return True
        if (strEvseStatusCode == "10"): # Reserved, Error
            return True
        if (strEvseStatusCode == "11"): # Reserved, Error
            return True
        return False # no critical error detected
            
    def sendChargeParameterDiscoveryReq(self):
        soc = str(self.hardwareInterface.getSoc())
        msg = addV2GTPHeader(self.exiEncode("EDE_"+self.sessionId + "_" + soc)) # EDE for Encode, Din, ChargeParameterDiscovery.
        self.addToTrace("responding " + prettyHexMessage(msg))
        self.Tcp.transmit(msg)
        
    def sendCableCheckReq(self):
        soc = str(self.hardwareInterface.getSoc())
        msg = addV2GTPHeader(self.exiEncode("EDF_"+self.sessionId + "_" + soc)) # EDF for Encode, Din, CableCheckReq
        self.addToTrace("responding " + prettyHexMessage(msg))
        self.Tcp.transmit(msg)
        # Since the response to the CableCheckRequest may need longer, inform the connection manager to be patient.
        # This makes sure, that the timeout of the state machine comes before the timeout of the connectionManager, so
        # that we enter the safe shutdown sequence as intended.
        self.connMgr.ApplOk(31)
    
    
    def sendCurrentDemandReq(self):
        soc = str(self.hardwareInterface.getSoc())
        EVTargetCurrent = str(self.hardwareInterface.getAccuMaxCurrent())
        EVTargetVoltage = str(self.hardwareInterface.getAccuMaxVoltage())
        msg = addV2GTPHeader(self.exiEncode("EDI_"+self.sessionId + "_" + soc + "_" + EVTargetCurrent + "_" + EVTargetVoltage )) # EDI for Encode, Din, CurrentDemandReq
        self.addToTrace("responding " + prettyHexMessage(msg))
        self.Tcp.transmit(msg)

    def sendWeldingDetectionReq(self):
        soc = str(self.hardwareInterface.getSoc())
        msg = addV2GTPHeader(self.exiEncode("EDJ_"+self.sessionId + "_" + soc)) # EDI for Encode, Din, WeldingDetectionReq
        self.addToTrace("responding " + prettyHexMessage(msg))
        self.Tcp.transmit(msg)
            
    def enterState(self, n):
        self.addToTrace("from " + str(self.state) + ":" + self.prettifyState(self.state) + " entering " + str(n) + ":" + self.prettifyState(n))
        self.state = n
        self.cyclesInState = 0
        
    def isTooLong(self):
        # The timeout handling function.
        limit = 66 # number of call cycles until timeout. Default 66 cycles with 30ms, means approx. 2 seconds.
        # This 2s is the specified timeout time for many messages, fitting to the
        # performance time of 1.5s. Exceptions see below.
        if (self.state==stateWaitForChargeParameterDiscoveryResponse):
            limit = 5*33 # On some charger models, the chargeParameterDiscovery needs more than a second. Wait at least 5s.
        if (self.state==stateWaitForCableCheckResponse):
            limit = 30*33 # CableCheck may need some time. Wait at least 30s.
        if (self.state==stateWaitForPreChargeResponse):
            limit = 30*33 # PreCharge may need some time. Wait at least 30s.
        if (self.state==stateWaitForPowerDeliveryResponse):
            limit = 6*33 # PowerDelivery may need some time. Wait at least 6s. On Compleo charger, observed more than 1s until response.
			# specified performance time is 4.5s (ISO)
        if (self.state==stateWaitForCurrentDemandResponse):
            limit = 5*33 # Test with 5s timeout. Just experimental.
            # The specified performance time is 25ms (ISO), the specified timeout 250ms.
        return (self.cyclesInState > limit)
        
    def stateFunctionNotYetInitialized(self):
        pass # nothing to do, just wait for external event for re-initialization

    def stateFunctionConnecting(self):
        if (self.cyclesInState<30): # The first second in the state just do nothing.
            return
        evseIp = self.addressManager.getSeccIp() # the chargers IP address which was announced in SDP
        seccTcpPort = self.addressManager.getSeccTcpPort() # the chargers TCP port which was announced in SDP
        self.addToTrace("Checkpoint301: connecting")
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
            self.publishStatus("TCP connected")
            self.isUserStopRequest = False
            self.enterState(stateConnected)
            return
    
    def stateFunctionConnected(self):
        # We have a freshly established TCP channel. We start the V2GTP/EXI communication now.
        # We just use the initial request message from the Ioniq. It contains one entry: DIN.
        self.addToTrace("Checkpoint400: Sending the initial SupportedApplicationProtocolReq")
        self.Tcp.transmit(addV2GTPHeader(exiHexToByteArray(exiHexDemoSupportedApplicationProtocolRequestIoniq)))
        # For testing purposes, we can also use the requests from other cars:
        #self.Tcp.transmit(addV2GTPHeader(exiHexToByteArray(exiHexDemoSupportedApplicationProtocolRequestTesla)))
        #self.Tcp.transmit(addV2GTPHeader(exiHexToByteArray(exiHexDemoSupportedApplicationProtocolRequestBMWiX3)))
        self.hardwareInterface.resetSimulation()
        self.enterState(stateWaitForSupportedApplicationProtocolResponse)
        
    def stateFunctionWaitForSupportedApplicationProtocolResponse(self):
        if (len(self.rxData)>0):
            self.addToTrace("In state WaitForSupportedApplicationProtocolResponse, received " + prettyHexMessage(self.rxData))
            if ((self.rxData[0]!=0x01) or (self.rxData[1]!=0xFE)):
                # it is no EXI data. Print it to log, it could be a TESTSUITE notification.
                self.addToTrace("TESTSUITE notification. Seems we are running a test case. TTTTTTTTTTTTTTTTTTTTTTT")
                if (len(self.rxData)<=20):
                    # it was the length of the testsuite notification. We are finished with this message.
                    self.rxData = []
                    return
                else:
                    # There was more data than the 20 byte testsuite notification. Most likely the EXI comes in the same message.
                    self.rxData = self.rxData[20:]
            exidata = removeV2GTPHeader(self.rxData)
            self.rxData = []
            strConverterResult = self.exiDecode(exidata, "Dh") # Decode Handshake-response
            self.addToTrace(strConverterResult)
            if (strConverterResult.find("supportedAppProtocolRes")>0):
                # todo: check the request content, and fill response parameters
                self.publishStatus("Schema negotiated")
                self.addToTrace("Checkpoint403: Schema negotiated. And Checkpoint500: Will send SessionSetupReq")
                self.addToTrace("EDA_"+self.evccid)
                msg = addV2GTPHeader(self.exiEncode("EDA_"+self.evccid)) # EDA for Encode, Din, SessionSetupReq
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
            strConverterResult = self.exiDecode(exidata, "DD") # Decode DIN
            self.addToTrace(strConverterResult)
            if (strConverterResult.find("SessionSetupRes")>0):
                # todo: check the request content, and fill response parameters
                strResponseCode = "na"
                try:
                    jsondict = json.loads(strConverterResult)
                    strSessionId = jsondict["header.SessionID"]
                    strResponseCode = jsondict["ResponseCode"]
                    self.addToTrace("Checkpoint506: The Evse decided for SessionId " + strSessionId)
                    self.publishStatus("Session established")
                    self.sessionId = strSessionId
                except:
                    self.addToTrace("ERROR: Could not decode the sessionID")
                if ((strResponseCode!="OK_NewSessionEstablished") and (strResponseCode!="OK")):
                    # According to the standard, the only valid response code is OK_NewSessionEstablished.
                    # But the ABB chargers use "OK", so we need to accept this, too. Discussed
                    # here: https://openinverter.org/forum/viewtopic.php?p=58399#p58399
                    self.addToTrace("Wrong response code. Aborting.")
                    self.enterState(stateUnrecoverableError)
                    return
                self.addToTrace("Will send ServiceDiscoveryReq")
                msg = addV2GTPHeader(self.exiEncode("EDB_"+self.sessionId)) # EDB for Encode, Din, ServiceDiscoveryRequest
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
            strConverterResult = self.exiDecode(exidata, "DD") # Decode DIN
            self.addToTrace(strConverterResult)
            if (strConverterResult.find("ServiceDiscoveryRes")>0):
                strResponseCode = "na"
                try:
                    jsondict = json.loads(strConverterResult)
                    strResponseCode = jsondict["ResponseCode"]
                except:
                    self.addToTrace("ERROR: Could not decode the ServiceDiscoveryResponse")
                if (strResponseCode!="OK"):
                    self.addToTrace("Wrong response code. Aborting.")
                    self.enterState(stateUnrecoverableError)
                    return
                self.publishStatus("ServDisc done")
                self.addToTrace("Will send ServicePaymentSelectionReq")
                msg = addV2GTPHeader(self.exiEncode("EDC_"+self.sessionId)) # EDC for Encode, Din, ServicePaymentSelection
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
            strConverterResult = self.exiDecode(exidata, "DD") # Decode DIN
            self.addToTrace(strConverterResult)
            if (strConverterResult.find("ServicePaymentSelectionRes")>0):
                # todo: check the request content, and fill response parameters
                strResponseCode = "na"
                try:
                    jsondict = json.loads(strConverterResult)
                    strResponseCode = jsondict["ResponseCode"]
                except:
                    self.addToTrace("ERROR: Could not decode the ServicePaymentSelectionResponse")
                if (strResponseCode!="OK"):
                    self.addToTrace("Wrong response code. Aborting.")
                    self.enterState(stateUnrecoverableError)
                    return
                self.publishStatus("ServPaySel done")
                self.addToTrace("Checkpoint530: Will send ContractAuthenticationReq")
                msg = addV2GTPHeader(self.exiEncode("EDL_"+self.sessionId)) # EDL for Encode, Din, ContractAuthenticationReq.
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
            strConverterResult = self.exiDecode(exidata, "DD") # Decode DIN
            self.addToTrace(strConverterResult)
            if (strConverterResult.find("ContractAuthenticationRes")>0):
                # In normal case, we can have two results here: either the Authentication is needed (the user
                # needs to authorize by RFID card or app, or something like this.
                # Or, the authorization is finished. This is shown by EVSEProcessing=Finished.
                strResponseCode = "na"
                try:
                    jsondict = json.loads(strConverterResult)
                    strResponseCode = jsondict["ResponseCode"]
                except:
                    self.addToTrace("ERROR: Could not decode the ContractAuthenticationResponse")
                if (strResponseCode!="OK"):
                    self.addToTrace("Wrong response code. Aborting.")
                    self.enterState(stateUnrecoverableError)
                    return
                if (strConverterResult.find('"EVSEProcessing": "Finished"')>0):
                    self.publishStatus("Auth finished")
                    self.addToTrace("Checkpoint538: Auth is Finished. Will send ChargeParameterDiscoveryReq")
                    self.sendChargeParameterDiscoveryReq()
                    self.numberOfChargeParameterDiscoveryReq = 1 # first message
                    self.enterState(stateWaitForChargeParameterDiscoveryResponse)
                else:
                    # Not (yet) finished.
                    if (self.numberOfContractAuthenticationReq>=120): # approx 120 seconds, maybe the user searches two minutes for his RFID card...
                        self.addToTrace("Authentication lasted too long. " + str(self.numberOfContractAuthenticationReq) + " Giving up.")
                        self.enterState(stateSequenceTimeout)
                    else:
                         # Try again.
                        self.numberOfContractAuthenticationReq += 1 # count the number of tries.
                        self.publishStatus("Waiting f Auth")
                        self.addToTrace("Not (yet) finished. Will again send ContractAuthenticationReq #" + str(self.numberOfContractAuthenticationReq))
                        msg = addV2GTPHeader(self.exiEncode("EDL_"+self.sessionId)) # EDL for Encode, Din, ContractAuthenticationReq.
                        self.addToTrace("responding " + prettyHexMessage(msg))
                        self.Tcp.transmit(msg)
                        # We just stay in the same state, until the timeout elapses.
                        self.enterState(stateWaitForContractAuthenticationResponse) 
        if (self.isTooLong()):
            # The timeout in case if nothing is received at all.
            self.enterState(stateSequenceTimeout)
        
    def stateFunctionWaitForChargeParameterDiscoveryResponse(self):
        if (self.cyclesInState<30): # The first second in the state just do nothing.
            return    
        if (len(self.rxData)>0):
            self.addToTrace("In state WaitForChargeParameterDiscoveryResponse, received " + prettyHexMessage(self.rxData))
            exidata = removeV2GTPHeader(self.rxData)
            self.rxData = []
            strConverterResult = self.exiDecode(exidata, "DD") # Decode DIN
            self.addToTrace(strConverterResult)
            if (strConverterResult.find("ChargeParameterDiscoveryRes")>0):
                strResponseCode = "na"
                strEVSEProcessing = "na"
                strEVSEStatusCode_text = "na"
                try:
                    jsondict = json.loads(strConverterResult)
                    strResponseCode = jsondict["ResponseCode"]
                    strEVSEProcessing =  jsondict["EVSEProcessing"]
                    strEVSEStatusCode_text = jsondict["EVSEStatusCode_text"]
                except:
                    self.addToTrace("ERROR: Could not decode the ChargeParameterDiscoveryResponse")
                if (strResponseCode!="OK"):
                    self.addToTrace("Wrong response code. Aborting.")
                    self.enterState(stateUnrecoverableError)
                    return
                # We can have three cases here:
                # (A) The charger needs more time to show the charge parameters. It does not say "EVSEProcessing": "Finished".
                # (B) The charger finished to tell the charge parameters, but still needs more time for internal purposes.
                #     It says "EVSEProcessing": "Finished", but also "EVSEStatusCode_text": "EVSE_NotReady". Observed and discussed
                #     here: https://openinverter.org/forum/viewtopic.php?p=58239#p58239.
                #     Update: This seems to be a normal case for Compleo, and NO reason to wait. So we go to the next step (cable check).
                # (C) The charger is really finished and able to continue with the next step (cable check).
                if ((strEVSEProcessing == "Finished")) :
                    # Case B and C
                    self.publishStatus("ChargeParams discovered")
                    self.addToTrace("Checkpoint550: ChargeParams are discovered. Will change to state C.")
                    #Report charger paramters
                    maxI = combineValueAndMultiplier(jsondict["EVSEMaximumCurrentLimit.Value"], jsondict["EVSEMaximumCurrentLimit.Multiplier"])
                    maxV = combineValueAndMultiplier(jsondict["EVSEMaximumVoltageLimit.Value"], jsondict["EVSEMaximumVoltageLimit.Multiplier"])
                    self.hardwareInterface.setChargerParameters(maxV, maxI)
                    # pull the CP line to state C here:
                    self.hardwareInterface.setStateC()
                    self.addToTrace("Checkpoint555: Locking the connector.")
                    self.hardwareInterface.triggerConnectorLocking()
                    self.enterState(stateWaitForConnectorLock)
                else:
                    # Not (yet) finished. Cases A and B.
                    if (self.numberOfChargeParameterDiscoveryReq>=60): # approx 60 seconds, should be sufficient for the charger to find its parameters... The ISO allows up to 55s reaction time and 60s timeout for "ongoing".
                        self.addToTrace("ChargeParameterDiscovery lasted too long. " + str(self.numberOfChargeParameterDiscoveryReq) + " Giving up.")
                        self.enterState(stateSequenceTimeout)
                    else:
                         # Try again.
                        self.numberOfChargeParameterDiscoveryReq += 1 # count the number of tries.
                        self.publishStatus("disc ChargeParams")
                        self.addToTrace("Not (yet) finished. Will again send ChargeParameterDiscoveryReq #" + str(self.numberOfChargeParameterDiscoveryReq))
                        self.sendChargeParameterDiscoveryReq()
                        # we stay in the same state
                        self.enterState(stateWaitForChargeParameterDiscoveryResponse)                
        if (self.isTooLong()):
            self.enterState(stateSequenceTimeout)

    def stateFunctionWaitForConnectorLock(self):
        if (self.hardwareInterface.isConnectorLocked()):
            self.addToTrace("Checkpoint560: Connector Lock confirmed. Will send CableCheckReq.")
            self.sendCableCheckReq()
            self.numberOfCableCheckReq = 1 # This is the first request.
            self.enterState(stateWaitForCableCheckResponse)
        if (self.isTooLong()):
            self.enterState(stateSequenceTimeout)
    
    def stateFunctionWaitForCableCheckResponse(self):
        if (self.cyclesInState<30): # The first second in the state just do nothing.
            return     
        if (len(self.rxData)>0):
            self.addToTrace("In state WaitForCableCheckResponse, received " + prettyHexMessage(self.rxData))
            exidata = removeV2GTPHeader(self.rxData)
            self.rxData = []
            strConverterResult = self.exiDecode(exidata, "DD") # Decode DIN
            self.addToTrace(strConverterResult)
            if (strConverterResult.find("CableCheckRes")>0):
                strResponseCode = "na"
                try:
                    jsondict = json.loads(strConverterResult)
                    strResponseCode = jsondict["ResponseCode"]
                    strEVSEProcessing = jsondict["EVSEProcessing"]
                    self.addToTrace("The CableCheck result is " + strResponseCode + " " + strEVSEProcessing)
                except:
                    self.addToTrace("ERROR: Could not decode the CableCheckRes")
                if (strResponseCode!="OK"):
                    self.addToTrace("Wrong response code. Aborting.")
                    self.enterState(stateUnrecoverableError)
                    return
                # We have two cases here:
                # 1) The charger says "cable check is finished and cable ok", by setting ResponseCode=OK and EVSEProcessing=Finished.
                # 2) Else: The charger says "need more time or cable not ok". In this case, we just run into timeout and start from the beginning.
                if ((strEVSEProcessing=="Finished") and (strResponseCode=="OK")):
                    self.publishStatus("CbleChck done")
                    self.addToTrace("The EVSE says that the CableCheck is finished and ok.")
                    self.addToTrace("Will send PreChargeReq")
                    soc = self.hardwareInterface.getSoc()
                    EVTargetVoltage = self.hardwareInterface.getAccuVoltage()
                    msg = addV2GTPHeader(self.exiEncode("EDG_"+self.sessionId+"_"+str(soc)+"_"+str(EVTargetVoltage))) # EDG for Encode, Din, PreChargeReq
                    self.addToTrace("responding " + prettyHexMessage(msg))
                    self.Tcp.transmit(msg)
                    self.connMgr.ApplOk(31) # PreChargeResponse may need longer. Inform the connection manager to be patient.
                    self.enterState(stateWaitForPreChargeResponse)
                else:
                    if (self.numberOfCableCheckReq>60): # approx 60s should be sufficient for cable check. The ISO allows up to 55s reaction time and 60s timeout for "ongoing".
                        self.addToTrace("CableCheck lasted too long. " + str(self.numberOfCableCheckReq) + " Giving up.")
                        self.enterState(stateSequenceTimeout)
                    else:    
                        # cable check not yet finished or finished with bad result -> try again
                        self.numberOfCableCheckReq += 1
                        self.publishStatus("CbleChck ongoing", format(self.hardwareInterface.getInletVoltage(),".0f") + "V")
                        self.addToTrace("Will again send CableCheckReq")
                        self.sendCableCheckReq()
                        # stay in the same state
                        self.enterState(stateWaitForCableCheckResponse)
                    
        if (self.isTooLong()):
            self.enterState(stateSequenceTimeout)

    def stateFunctionWaitForPreChargeResponse(self):
        self.hardwareInterface.simulatePreCharge()
        if (self.DelayCycles>0):
            self.DelayCycles-=1
            return    
        if (len(self.rxData)>0):
            self.addToTrace("In state WaitForPreChargeResponse, received " + prettyHexMessage(self.rxData))
            exidata = removeV2GTPHeader(self.rxData)
            self.rxData = []
            strConverterResult = self.exiDecode(exidata, "DD") # Decode DIN
            self.addToTrace(strConverterResult)
            if (strConverterResult.find("PreChargeRes")>0):
                u = 0 # a default voltage of 0V in case we cannot convert the actual value
                strResponseCode = "na"
                strEVSEStatusCode = "0" # default in case the decoding does not work
                try:
                    jsondict = json.loads(strConverterResult)
                    strResponseCode = jsondict["ResponseCode"]
                    strEVSEPresentVoltageValue = jsondict["EVSEPresentVoltage.Value"]
                    strEVSEPresentVoltageMultiplier = jsondict["EVSEPresentVoltage.Multiplier"]
                    u = combineValueAndMultiplier(strEVSEPresentVoltageValue, strEVSEPresentVoltageMultiplier)
                    self.callbackShowStatus(format(u,".1f"), "EVSEPresentVoltage")
                    strEVSEStatusCode = jsondict["DC_EVSEStatus.EVSEStatusCode"]
                except:
                    self.addToTrace("ERROR: Could not decode the PreChargeResponse")
                self.addToTrace("PreChargeResponse received.")
                if (strResponseCode!="OK"):
                    self.addToTrace("Wrong response code. Aborting.")
                    self.enterState(stateUnrecoverableError)
                    return
                if (self.isErrorEvseStatusCode(strEVSEStatusCode)):
                    self.enterState(stateUnrecoverableError)
                    return
                if (getConfigValueBool("use_evsepresentvoltage_for_precharge_end")):
                    # We want to use the EVSEPresentVoltage, which was reported by the charger, as end-criteria for the precharging.
                    s = "EVSEPresentVoltage " + str(u) + "V, "
                else:
                    # We want to use the physically measured inlet voltage as end-criteria for the precharging.
                    u = self.hardwareInterface.getInletVoltage()
                    s = "U_Inlet " + str(u) + "V, "
                s= s + "U_Accu " + str(self.hardwareInterface.getAccuVoltage()) + "V"
                self.addToTrace(s)
                if (abs(u-self.hardwareInterface.getAccuVoltage()) < float(getConfigValue("u_delta_max_for_end_of_precharge"))):
                    self.addToTrace("Difference between accu voltage and inlet voltage is small.")
                    self.publishStatus("PreCharge done")
                    if (self.isLightBulbDemo):
                        # For light-bulb-demo, nothing to do here.
                        self.addToTrace("This is a light bulb demo. Do not turn-on the relay at end of precharge.")
                    else:
                        # In real-world-case, turn the power relay on.
                        self.addToTrace("Checkpoint590: Turning the contactors on.")
                        self.hardwareInterface.setPowerRelayOn()
                    self.DelayCycles = 10 # 10*33ms = 330ms waiting for contactors
                    self.enterState(stateWaitForContactorsClosed)
                else:
                    self.publishStatus("PreChrge ongoing", format(u, ".0f") + "V")
                    self.addToTrace("Difference too big. Continuing PreCharge.")
                    soc = self.hardwareInterface.getSoc()
                    EVTargetVoltage = self.hardwareInterface.getAccuVoltage()
                    msg = addV2GTPHeader(self.exiEncode("EDG_"+self.sessionId+"_"+str(soc)+"_"+str(EVTargetVoltage))) # EDG for Encode, Din, PreChargeReq
                    self.addToTrace("responding " + prettyHexMessage(msg))
                    self.Tcp.transmit(msg)
                    self.DelayCycles=15 # wait with the next evaluation approx half a second
        if (self.isTooLong()):
            self.enterState(stateSequenceTimeout)
            
    def stateFunctionWaitForContactorsClosed(self):
        if (self.DelayCycles>0):
            self.DelayCycles-=1
            return
        if (self.isLightBulbDemo):
            readyForNextState=1 # if it's just a bulb demo, we do not wait for contactor, because it is not switched in this moment.
        else:
            readyForNextState = self.hardwareInterface.getPowerRelayConfirmation() # check if the contactor is closed
            if (readyForNextState):
                self.addToTrace("Contactors are confirmed to be closed.")
                self.publishStatus("Contactors ON")
        if (readyForNextState):
            self.addToTrace("Sending PowerDeliveryReq.")
            soc = self.hardwareInterface.getSoc()
            msg = addV2GTPHeader(self.exiEncode("EDH_"+self.sessionId+"_"+ str(soc) + "_" + "1")) # EDH for Encode, Din, PowerDeliveryReq, ON
            self.wasPowerDeliveryRequestedOn=True
            self.addToTrace("responding " + prettyHexMessage(msg))
            self.Tcp.transmit(msg)
            self.enterState(stateWaitForPowerDeliveryResponse)
        if (self.isTooLong()):
            self.enterState(stateSequenceTimeout)
    
    def stateFunctionWaitForPowerDeliveryResponse(self):
        if (len(self.rxData)>0):
            self.addToTrace("In state WaitForPowerDeliveryRes, received " + prettyHexMessage(self.rxData))
            exidata = removeV2GTPHeader(self.rxData)
            self.rxData = []
            strConverterResult = self.exiDecode(exidata, "DD") # Decode DIN
            self.addToTrace(strConverterResult)
            if (strConverterResult.find("PowerDeliveryRes")>0):
                strResponseCode = "na"
                try:
                    jsondict = json.loads(strConverterResult)
                    strResponseCode = jsondict["ResponseCode"]
                except:
                    self.addToTrace("ERROR: Could not decode the PowerDeliveryResponse")
                if (strResponseCode!="OK"):
                    self.addToTrace("Wrong response code. Aborting.")
                    self.enterState(stateUnrecoverableError)
                    return
                if (self.wasPowerDeliveryRequestedOn):
                    self.publishStatus("PwrDelvy ON success")
                    self.addToTrace("Checkpoint700: Starting the charging loop with CurrentDemandReq")
                    self.sendCurrentDemandReq()
                    self.enterState(stateWaitForCurrentDemandResponse)
                else:
                    # We requested "OFF". So we turn-off the Relay and continue with the Welding detection.
                    self.publishStatus("PwrDelvry OFF success")
                    self.addToTrace("Checkpoint806: PowerDelivery Off confirmed.")
                    self.addToTrace("Checkpoint810: Changing CP line to State B.")
                    # set the CP line to B 
                    self.hardwareInterface.setStateB()
                    self.addToTrace("Turning off the relay and starting the WeldingDetection")
                    self.hardwareInterface.setPowerRelayOff()
                    self.hardwareInterface.setRelay2Off()
                    self.isBulbOn = False
                    self.sendWeldingDetectionReq()
                    self.enterState(stateWaitForWeldingDetectionResponse)
        if (self.isTooLong()):
            self.enterState(stateSequenceTimeout)

    def stateFunctionWaitForCurrentDemandResponse(self):
        if (len(self.rxData)>0):
            self.addToTrace("In state WaitForCurrentDemandRes, received " + prettyHexMessage(self.rxData))
            exidata = removeV2GTPHeader(self.rxData)
            self.rxData = []
            strConverterResult = self.exiDecode(exidata, "DD") # Decode DIN
            self.addToTrace(strConverterResult)
            if (strConverterResult.find("CurrentDemandRes")>0):
                strResponseCode = "na"
                u = 0 # a default voltage of 0V in case we cannot convert the actual value
                strEVSEStatusCode = "0" # default in case the decoding does not work
                try:
                    jsondict = json.loads(strConverterResult)
                    strResponseCode = jsondict["ResponseCode"]
                    strEVSEPresentVoltageValue = jsondict["EVSEPresentVoltage.Value"]
                    strEVSEPresentVoltageMultiplier = jsondict["EVSEPresentVoltage.Multiplier"]
                    strEVSEPresentCurrentValue = jsondict["EVSEPresentCurrent.Value"]
                    strEVSEPresentCurrentMultiplier = jsondict["EVSEPresentCurrent.Multiplier"]
                    u = combineValueAndMultiplier(strEVSEPresentVoltageValue, strEVSEPresentVoltageMultiplier)
                    i = combineValueAndMultiplier(strEVSEPresentCurrentValue, strEVSEPresentCurrentMultiplier)
                    self.callbackShowStatus(format(u,".1f"), "EVSEPresentVoltage")
                    strEVSEStatusCode = jsondict["DC_EVSEStatus.EVSEStatusCode"]
                    self.hardwareInterface.setChargerVoltageAndCurrent(u, i)
                except:
                    self.addToTrace("ERROR: Could not decode the PreChargeResponse")
                if (strResponseCode!="OK"):
                    self.addToTrace("Wrong response code. Aborting.")
                    self.enterState(stateUnrecoverableError)
                    return
                if (self.isErrorEvseStatusCode(strEVSEStatusCode)):
                    self.enterState(stateUnrecoverableError)
                    return
                if (getConfigValueBool("use_physical_inlet_voltage_during_chargeloop")):
                    # Instead of using the voltage which is reported by the charger, use the physically measured.
                    u = self.hardwareInterface.getInletVoltage()
                # as long as the accu is not full and no stop-demand from the user, we continue charging
                if (self.hardwareInterface.getIsAccuFull() or self.isUserStopRequest):
                    if (self.hardwareInterface.getIsAccuFull()):
                        self.publishStatus("Accu full")
                        self.addToTrace("Accu is full. Sending PowerDeliveryReq Stop.")
                    else:
                        self.publishStatus("User req stop")
                        self.addToTrace("User requested stop. Sending PowerDeliveryReq Stop.")
                    soc = self.hardwareInterface.getSoc()
                    msg = addV2GTPHeader(self.exiEncode("EDH_"+self.sessionId+"_"+ str(soc) + "_" + "0")) # EDH for Encode, Din, PowerDeliveryReq, OFF
                    self.wasPowerDeliveryRequestedOn=False
                    self.addToTrace("responding " + prettyHexMessage(msg))
                    self.Tcp.transmit(msg)
                    self.enterState(stateWaitForPowerDeliveryResponse)
                else:
                    # continue charging loop
                    self.publishStatus("Charging", format(u, ".0f") + "V", format(self.hardwareInterface.getSoc(), ".1f") + "%")
                    self.sendCurrentDemandReq()
                    self.enterState(stateWaitForCurrentDemandResponse)
        if (self.isLightBulbDemo):
            if (self.cyclesLightBulbDelay<=33*2):
                self.cyclesLightBulbDelay+=1
            else:
                if (not self.isBulbOn):
                    self.addToTrace("This is a light bulb demo. Turning-on the bulb when 2s in the main charging loop.")
                    self.hardwareInterface.setPowerRelayOn()   
                    self.hardwareInterface.setRelay2On() 
                    self.isBulbOn = True
        if (self.isTooLong()):
            self.enterState(stateSequenceTimeout)

    def stateFunctionWaitForWeldingDetectionResponse(self):
        if (len(self.rxData)>0):
            self.addToTrace("In state WaitForWeldingDetectionResponse, received " + prettyHexMessage(self.rxData))
            exidata = removeV2GTPHeader(self.rxData)
            self.rxData = []
            strConverterResult = self.exiDecode(exidata, "DD") # Decode DIN
            self.addToTrace(strConverterResult)
            if (strConverterResult.find("WeldingDetectionRes")>0):
                    strResponseCode = "na"
                    # todo: add real welding detection here, run in welding detection loop until finished.
                    self.publishStatus("WldingDet done")
                    self.addToTrace("Sending SessionStopReq")                    
                    msg = addV2GTPHeader(self.exiEncode("EDK_"+self.sessionId)) # EDI for Encode, Din, SessionStopReq
                    self.addToTrace("responding " + prettyHexMessage(msg))
                    self.Tcp.transmit(msg)
                    self.enterState(stateWaitForSessionStopResponse)
        if (self.isTooLong()):
            self.enterState(stateSequenceTimeout)

    def stateFunctionWaitForSessionStopResponse(self):
        if (len(self.rxData)>0):
            self.addToTrace("In state WaitForSessionStopRes, received " + prettyHexMessage(self.rxData))
            exidata = removeV2GTPHeader(self.rxData)
            self.rxData = []
            strConverterResult = self.exiDecode(exidata, "DD") # Decode DIN
            self.addToTrace(strConverterResult)
            if (strConverterResult.find("SessionStopRes")>0):
                strResponseCode = "na"
                # req -508
                # Unlocking of the connector in the next state.
                self.publishStatus("Stopped normally")
                self.addToTrace("Charging is finished")
                self.enterState(stateChargingFinished)
        if (self.isTooLong()):
            self.enterState(stateSequenceTimeout)
    
    def stateFunctionChargingFinished(self):
        # charging is finished.
        # Finally unlock the connector
        self.addToTrace("Charging successfully finished. Unlocking the connector")
        self.hardwareInterface.triggerConnectorUnlocking()
        testsuite_reportstatus("TSRS_ChargingFinished")
        self.enterState(stateEnd)

    def stateFunctionSequenceTimeout(self):
        # Here we end, if we run into a timeout in the state machine.
        self.publishStatus("ERROR Timeout")
        # Initiate the safe-shutdown-sequence.
        self.addToTrace("Safe-shutdown-sequence: setting state B")
        self.hardwareInterface.setStateB() # setting CP line to B disables in the charger the current flow.
        self.DelayCycles = 66 # 66*30ms=2s for charger shutdown
        self.enterState(stateSafeShutDownWaitForChargerShutdown)
        
    def stateFunctionUnrecoverableError(self):
        # Here we end, if the EVSE reported an error code, which terminates the charging session.
        self.publishStatus("ERROR reported")
        # Initiate the safe-shutdown-sequence.
        self.addToTrace("Safe-shutdown-sequence: setting state B")
        self.hardwareInterface.setStateB() # setting CP line to B disables in the charger the current flow.
        self.DelayCycles = 66 # 66*30ms=2s for charger shutdown
        self.enterState(stateSafeShutDownWaitForChargerShutdown)

    def stateFunctionSafeShutDownWaitForChargerShutdown(self):
        # wait state, to give the charger the time to stop the current.
        self.connMgr.ApplOk() # Trigger the communication manager, so that it does not disturb our safe-shutdown.
        if (self.DelayCycles>0):
            self.DelayCycles-=1
            return
        # Now the current flow is stopped by the charger. We can safely open the contactors:
        self.addToTrace("Safe-shutdown-sequence: opening contactors")
        self.hardwareInterface.setPowerRelayOff()
        self.hardwareInterface.setRelay2Off()
        self.DelayCycles = 33 # 33*30ms=1s for opening the contactors
        self.enterState(stateSafeShutDownWaitForContactorsOpen)

    def stateFunctionSafeShutDownWaitForContactorsOpen(self):
        # wait state, to give the contactors the time to open.
        self.connMgr.ApplOk() # Trigger the communication manager, so that it does not disturb our safe-shutdown.
        if (self.DelayCycles>0):
            self.DelayCycles-=1
            return    
        # Finally, when we have no current and no voltage, unlock the connector
        self.addToTrace("Safe-shutdown-sequence: unlocking the connector")
        self.hardwareInterface.triggerConnectorUnlocking()
        testsuite_reportstatus("TSRS_SafeShutdownFinished")
        # This is the end of the safe-shutdown-sequence. 
        self.enterState(stateEnd)

    def stateFunctionEnd(self):
        # Just stay here, until we get re-initialized after a new SLAC/SDP.
        pass

    
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
            stateWaitForConnectorLock: stateFunctionWaitForConnectorLock,
            stateWaitForCableCheckResponse: stateFunctionWaitForCableCheckResponse,
            stateWaitForPreChargeResponse: stateFunctionWaitForPreChargeResponse,
            stateWaitForContactorsClosed: stateFunctionWaitForContactorsClosed,
            stateWaitForPowerDeliveryResponse: stateFunctionWaitForPowerDeliveryResponse,
            stateWaitForCurrentDemandResponse: stateFunctionWaitForCurrentDemandResponse,
            stateWaitForWeldingDetectionResponse: stateFunctionWaitForWeldingDetectionResponse,
            stateWaitForSessionStopResponse: stateFunctionWaitForSessionStopResponse,
            stateChargingFinished: stateFunctionChargingFinished,
            stateUnrecoverableError: stateFunctionUnrecoverableError,
            stateSequenceTimeout: stateFunctionSequenceTimeout,
            stateSafeShutDownWaitForChargerShutdown: stateFunctionSafeShutDownWaitForChargerShutdown,
            stateSafeShutDownWaitForContactorsOpen: stateFunctionSafeShutDownWaitForContactorsOpen,
            stateEnd: stateFunctionEnd
        }

    def stopCharging(self):
        # API function to stop the charging.
        self.isUserStopRequest = True
        

    def reInit(self):
        self.addToTrace("re-initializing fsmPev") 
        self.Tcp.disconnect()
        self.hardwareInterface.setStateB()
        self.hardwareInterface.setPowerRelayOff()
        self.hardwareInterface.setRelay2Off()
        self.isBulbOn = False
        self.cyclesLightBulbDelay = 0
        self.state = stateConnecting
        self.cyclesInState = 0
        self.rxData = []
        
    def __init__(self, addressManager, connMgr, callbackAddToTrace, hardwareInterface, callbackShowStatus):
        self.callbackAddToTrace = callbackAddToTrace
        self.callbackShowStatus = callbackShowStatus
        self.addToTrace("initializing fsmPev") 
        self.exiLogFile = open('PevExiLog.txt', 'a')
        self.exiLogFile.write("init\n")
        self.Tcp = pyPlcTcpSocket.pyPlcTcpClientSocket(self.callbackAddToTrace)
        self.addressManager = addressManager
        self.connMgr = connMgr
        self.hardwareInterface = hardwareInterface
        self.state = stateNotYetInitialized
        self.sessionId = "DEAD55AADEAD55AA"
        self.evccid = addressManager.getLocalMacAsTwelfCharString()
        self.cyclesInState = 0
        self.DelayCycles = 0
        self.rxData = []        
        self.isLightBulbDemo = getConfigValueBool("light_bulb_demo")
        self.isBulbOn = False
        self.cyclesLightBulbDelay = 0
        self.isUserStopRequest = False
        # we do NOT call the reInit, because we want to wait with the connection until external trigger comes
                
    def __del__(self):
        self.exiLogFile.write("closing\n")
        self.exiLogFile.close()
        
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
        

