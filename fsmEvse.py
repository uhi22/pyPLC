# State machine for the charger
#
#

#------------------------------------------------------------

import pyPlcTcpSocket
import time # for time.sleep()
from helpers import prettyHexMessage, combineValueAndMultiplier
from mytestsuite import *
from random import random
from exiConnector import * # for EXI data handling/converting

stateWaitForSupportedApplicationProtocolRequest = 0
stateWaitForSessionSetupRequest = 1
stateWaitForServiceDiscoveryRequest = 2
stateWaitForServicePaymentSelectionRequest = 3
stateWaitForFlexibleRequest = 4
stateWaitForChargeParameterDiscoveryRequest = 5
stateWaitForCableCheckRequest = 6
stateWaitForPreChargeRequest = 7
stateWaitForPowerDeliveryRequest = 8

class fsmEvse():
    def addToTrace(self, s):
        self.callbackAddToTrace("[EVSE] " + s)

    def publishStatus(self, s):
        self.callbackShowStatus(s, "evseState")
        self.hardwareInterface.displayState(s)

    def publishSoCs(self, current_soc: int, full_soc: int = -1, energy_capacity: int = -1, energy_request: int = -1, evccid: str = "", origin: str = ""):
        self.hardwareInterface.displaySoc(current_soc)
        if self.callbackSoCStatus is not None:
            self.callbackSoCStatus(current_soc, full_soc, energy_capacity, energy_request, self.evccid, origin)

    def enterState(self, n):
        self.addToTrace("from " + str(self.state) + " entering " + str(n))
        if (self.state!=0) and (n==0):
            self.publishStatus("Waiting f AppHandShake")
        self.state = n
        self.cyclesInState = 0

    def isTooLong(self):
        # The timeout handling function.
        return (self.cyclesInState > 100) # 100*33ms=3.3s

    def showDecodedTransmitMessage(self, msg):
        # decodes the transmit message to show it in the trace.
        # This is inefficient, because it calls the exi decoder via the slow
        # command line interface, while DEcoding for the transmit data is
        # technically not necessary. Only for logging. In case this
        # introduces timing problems, just remove the three lines below.
        exidataTx = removeV2GTPHeader(msg)
        strConverterResultTx = exiDecode(exidataTx, "D"+self.schemaSelection)
        self.addToTrace(strConverterResultTx)


    def stateFunctionWaitForSupportedApplicationProtocolRequest(self):
        if (len(self.rxData)>0):
            self.addToTrace("In state WaitForSupportedApplicationProtocolRequest, received " + prettyHexMessage(self.rxData))
            exidata = removeV2GTPHeader(self.rxData)
            self.rxData = []
            strConverterResult = exiDecode(exidata, "DH") # Decode Handshake-request
            self.addToTrace(strConverterResult)
            if (strConverterResult.find("supportedAppProtocolReq")>0):
                nDinSchemaID = 255 # invalid default value
                nIso1SchemaID = 255
                try:
                    jsondict = json.loads(strConverterResult)
                    nAppProtocol_ArrayLen = int(jsondict["AppProtocol_arrayLen"])
                    self.addToTrace("The car supports " + str(nAppProtocol_ArrayLen) + " schemas.")
                    for i in range(nAppProtocol_ArrayLen):
                        strNameSpace = jsondict["NameSpace_"+str(i)]
                        nSchemaId = int(jsondict["SchemaID_"+str(i)])
                        self.addToTrace("The NameSpace " + strNameSpace + " has SchemaID " + str(nSchemaId))
                        if (strNameSpace.find(":din:70121:")>0):
                            nDinSchemaID = nSchemaId
                        if (strNameSpace.find(":iso:15118:2:2013")>0):
                            nIso1SchemaID = nSchemaId
                except:
                    self.addToTrace("ERROR: Could not decode the supportedAppProtocolReq")
                # Strategy for schema selection: pyPLC preferes DIN. If the car does not announce DIN,
                # then pyPLC looks for ISO1. If this is also not announced by the car, pyPLC will not
                # send a handshake response.
                # This means: pyPLC does NOT care for the priority sent by the car. It uses the own
                # priority "DIN over ISO1". Reason: DIN is proven-in-use, the ISO implementation still
                # work-in-progress.
                if (nDinSchemaID<255):
                    self.addToTrace("Detected DIN")
                    # TESTSUITE: When the EVSE received the Handshake, it selects a new test case.
                    testsuite_choose_testcase()
                    # Eh for encode handshake, SupportedApplicationProtocolResponse, with SchemaID as parameter
                    msg = addV2GTPHeader(exiEncode("Eh__"+str(nDinSchemaID)))
                    self.addToTrace("responding " + prettyHexMessage(msg))
                    self.Tcp.transmit(msg)
                    self.publishStatus("Schema negotiated")
                    self.schemaSelection = "D" # D for DIN
                    self.enterState(stateWaitForSessionSetupRequest)
                else:
                    if (nIso1SchemaID<255):
                        self.addToTrace("Detected ISO1 (aka ISO 2013)")
                        # TESTSUITE: When the EVSE received the Handshake, it selects a new test case.
                        testsuite_choose_testcase()
                        # Eh for encode handshake, SupportedApplicationProtocolResponse, with SchemaID as parameter
                        msg = addV2GTPHeader(exiEncode("Eh__"+str(nIso1SchemaID)))
                        self.addToTrace("responding " + prettyHexMessage(msg))
                        self.Tcp.transmit(msg)
                        self.publishStatus("Schema negotiated")
                        self.schemaSelection = "1" # 1 for ISO1
                        self.enterState(stateWaitForSessionSetupRequest)
                    else:
                        self.addToTrace("Error: The connected car does not support DIN or ISO1. At the moment, the pyPLC only supports DIN and ISO1.")

    def stateFunctionWaitForSessionSetupRequest(self):
        if (len(self.rxData)>0):
            self.simulatedPresentVoltage = 0
            self.addToTrace("In state WaitForSessionSetupRequest, received " + prettyHexMessage(self.rxData))
            exidata = removeV2GTPHeader(self.rxData)
            self.rxData = []
            strConverterResult = exiDecode(exidata, "D"+self.schemaSelection) # decodes DIN or ISO1
            self.addToTrace(strConverterResult)
            if (strConverterResult.find("SessionSetupReq")>0):
                msg = addV2GTPHeader(exiEncode("E"+self.schemaSelection+"a")) # EDa for Encode, Din, SessionSetupResponse
                if (testsuite_faultinjection_is_triggered(TC_EVSE_ResponseCode_SequenceError_for_SessionSetup)):
                    # send a SessionSetupResponse with Responsecode SequenceError
                    msg = addV2GTPHeader("809a0232417b661514a4cb91e0A02d0691559529548c0841e0fc1af4507460c0")
                self.addToTrace("responding " + prettyHexMessage(msg))
                self.showDecodedTransmitMessage(msg)
                self.Tcp.transmit(msg)
                self.publishStatus("Session established")
                self.enterState(stateWaitForServiceDiscoveryRequest)
                jsondict = json.loads(strConverterResult)
                self.evccid = jsondict.get("EVCCID", "")

        if (self.isTooLong()):
            self.enterState(0)

    def stateFunctionWaitForServiceDiscoveryRequest(self):
        if (len(self.rxData)>0):
            self.addToTrace("In state WaitForServiceDiscoveryRequest, received " + prettyHexMessage(self.rxData))
            exidata = removeV2GTPHeader(self.rxData)
            self.rxData = []
            strConverterResult = exiDecode(exidata, "D"+self.schemaSelection) # decodes DIN or ISO1
            self.addToTrace(strConverterResult)
            if (strConverterResult.find("ServiceDiscoveryReq")>0):
                # todo: check the request content, and fill response parameters
                msg = addV2GTPHeader(exiEncode("E"+self.schemaSelection+"b")) # EDb for Encode, Din, ServiceDiscoveryResponse
                if (testsuite_faultinjection_is_triggered(TC_EVSE_ResponseCode_SequenceError_for_ServiceDiscoveryRes)):
                    # send a ServiceDiscoveryRes with Responsecode SequenceError
                    msg = addV2GTPHeader("809a021a3b7c417774813311a0A120024100c4")
                self.addToTrace("responding " + prettyHexMessage(msg))
                self.showDecodedTransmitMessage(msg)
                self.Tcp.transmit(msg)
                self.publishStatus("Services discovered")
                self.enterState(stateWaitForServicePaymentSelectionRequest)
        if (self.isTooLong()):
            self.enterState(0)

    def stateFunctionWaitForServicePaymentSelectionRequest(self):
        if (len(self.rxData)>0):
            self.addToTrace("In state WaitForServicePaymentSelectionRequest, received " + prettyHexMessage(self.rxData))
            exidata = removeV2GTPHeader(self.rxData)
            self.rxData = []
            strConverterResult = exiDecode(exidata, "D"+self.schemaSelection) # decodes DIN or ISO1
            self.addToTrace(strConverterResult)
            if (self.schemaSelection=="D"):
                strMessageName = "ServicePaymentSelectionReq" # This is the original name in DIN
            else:
                strMessageName = "PaymentServiceSelectionReq" # In ISO1, they use a slightly different name for the same thing.
            if (strConverterResult.find(strMessageName)>0):
                msg = addV2GTPHeader(exiEncode("E"+self.schemaSelection+"c")) # EDc for Encode, Din, ServicePaymentSelectionResponse
                if (testsuite_faultinjection_is_triggered(TC_EVSE_ResponseCode_SequenceError_for_ServicePaymentSelectionRes)):
                    # send a ServicePaymentSelectionRes with Responsecode SequenceError
                    msg = addV2GTPHeader("809a021a3b7c417774813311c0A0")
                self.addToTrace("responding " + prettyHexMessage(msg))
                self.showDecodedTransmitMessage(msg)
                self.Tcp.transmit(msg)
                self.publishStatus("ServicePayment selected")
                self.enterState(stateWaitForFlexibleRequest) # todo: not clear, what is specified. The Ioniq sends PowerDeliveryReq as next.
        if (self.isTooLong()):
            self.enterState(0)

    def stateFunctionWaitForFlexibleRequest(self):
        if (len(self.rxData)>0):
            self.addToTrace("In state WaitForFlexibleRequest, received " + prettyHexMessage(self.rxData))
            exidata = removeV2GTPHeader(self.rxData)
            self.rxData = []
            strConverterResult = exiDecode(exidata, "D"+self.schemaSelection) # decodes DIN or ISO1
            self.addToTrace(strConverterResult)
            if (strConverterResult.find("PowerDeliveryReq")>0):
                # todo: check the request content, and fill response parameters
                self.addToTrace("Received PowerDeliveryReq. Extracting SoC parameters")
                jsondict = json.loads(strConverterResult)
                current_soc = int(jsondict.get("EVRESSSOC", -1))
                self.publishSoCs(current_soc, origin="PowerDeliveryReq")
                msg = addV2GTPHeader(exiEncode("E"+self.schemaSelection+"h")) # EDh for Encode, Din, PowerDeliveryResponse
                if (testsuite_faultinjection_is_triggered(TC_EVSE_ResponseCode_Failed_for_PowerDeliveryRes)):
                    # send a PowerDeliveryResponse with Responsecode Failed
                    msg = addV2GTPHeader("809a0125e6cecc51408420400000")
                self.addToTrace("responding " + prettyHexMessage(msg))
                self.showDecodedTransmitMessage(msg)
                self.publishStatus("PowerDelivery")
                self.Tcp.transmit(msg)
                self.enterState(stateWaitForFlexibleRequest) # todo: not clear, what is specified in DIN
            if (strConverterResult.find("ChargeParameterDiscoveryReq")>0):
                self.addToTrace("Received ChargeParameterDiscoveryReq. Extracting SoC parameters via DC")
                jsondict = json.loads(strConverterResult)
                current_soc = int(jsondict.get("DC_EVStatus.EVRESSSOC", -1))
                full_soc = int(jsondict.get("FullSOC", -1))
                energy_capacity = int(jsondict.get("EVEnergyCapacity.Value", -1))
                energy_request = int(jsondict.get("EVEnergyRequest.Value", -1))
                self.publishSoCs(current_soc, full_soc, energy_capacity, energy_request, origin="ChargeParameterDiscoveryReq")

                # todo: check the request content, and fill response parameters
                msg = addV2GTPHeader(exiEncode("E"+self.schemaSelection+"e")) # EDe for Encode, Din, ChargeParameterDiscoveryResponse
                if (testsuite_faultinjection_is_triggered(TC_EVSE_ResponseCode_ServiceSelectionInvalid_for_ChargeParameterDiscovery)):
                    # send a ChargeParameterDiscoveryResponse with Responsecode ServiceSelectionInvalid
                    msg = addV2GTPHeader("809a0125e6cecd50810001ec00201004051828758405500080000101844138101c2432c04081436c900c0c000041435ecc044606000200")
                self.addToTrace("responding " + prettyHexMessage(msg))
                self.showDecodedTransmitMessage(msg)
                self.publishStatus("ChargeParamDiscovery")
                self.Tcp.transmit(msg)
                self.nCableCheckLoops = 0 # start with a fresh full cable check
                self.enterState(stateWaitForFlexibleRequest) # todo: not clear, what is specified in DIN
            if (strConverterResult.find("CableCheckReq")>0):
                # todo: check the request content, and fill response parameters
                # todo: make a real cable check, and while it is ongoing, send "Ongoing".
                self.addToTrace("Received CableCheckReq. Extracting SoC parameters via DC")
                jsondict = json.loads(strConverterResult)
                current_soc = int(jsondict.get("DC_EVStatus.EVRESSSOC", -1))
                self.publishSoCs(current_soc, -1, -1, origin="CableCheckReq")
                if (self.blChargeStopTrigger == 1 or self.hardwareInterface.stopRequest()):
                    strCableCheckOngoing = "1"
                elif (self.nCableCheckLoops<5):
                    self.nCableCheckLoops+=1
                    strCableCheckOngoing = "1"
                else:
                    strCableCheckOngoing = "0" # Now the cable check is finished.
                msg = addV2GTPHeader(exiEncode("E"+self.schemaSelection+"f_"+strCableCheckOngoing)) # EDf for Encode, Din, CableCheckResponse
                if (testsuite_faultinjection_is_triggered(TC_EVSE_ResponseCode_Failed_for_CableCheckRes)):
                    # send a CableCheckResponse with Responsecode Failed
                    msg = addV2GTPHeader("809a0125e6cecc5020804080000400")
                self.addToTrace("responding " + prettyHexMessage(msg))
                self.showDecodedTransmitMessage(msg)
                self.publishStatus("CableCheck")
                if (not testsuite_faultinjection_is_triggered(TC_EVSE_Timeout_during_CableCheck)):
                    self.Tcp.transmit(msg)
                self.enterState(stateWaitForFlexibleRequest) # todo: not clear, what is specified in DIN
            if (strConverterResult.find("PreChargeReq")>0):
                # check the request content, and fill response parameters
                uTarget = 220 # default in case we cannot decode the requested voltage
                try:
                    jsondict = json.loads(strConverterResult)
                    strEVTargetVoltageValue = jsondict["EVTargetVoltage.Value"]
                    strEVTargetVoltageMultiplier = jsondict["EVTargetVoltage.Multiplier"]
                    uTarget = combineValueAndMultiplier(strEVTargetVoltageValue, strEVTargetVoltageMultiplier)
                    self.addToTrace("EV wants EVTargetVoltage " + str(uTarget))
                except:
                    self.addToTrace("ERROR: Could not decode the PreChargeReq")

                # simulating preCharge
                if (self.simulatedPresentVoltage<uTarget/2):
                    self.simulatedPresentVoltage = uTarget/2
                if (self.simulatedPresentVoltage<uTarget-30):
                    self.simulatedPresentVoltage += 20
                if (self.simulatedPresentVoltage<uTarget):
                    self.simulatedPresentVoltage += 5
                    
                if getConfigValueBool('evse_simulate_precharge'):
                    strPresentVoltage = str(int(self.simulatedPresentVoltage*10)/10) # "345"
                else:
                    strPresentVoltage = str(self.hardwareInterface.getInletVoltage())

                # in case we control a real power supply: give the precharge target to it
                self.hardwareInterface.setPowerSupplyVoltageAndCurrent(uTarget, 1)
                self.callbackShowStatus(strPresentVoltage, "EVSEPresentVoltage")
                msg = addV2GTPHeader(exiEncode("E"+self.schemaSelection+"g_"+strPresentVoltage)) # EDg for Encode, Din, PreChargeResponse
                if (testsuite_faultinjection_is_triggered(TC_EVSE_Shutdown_during_PreCharge)):
                    # send a PreChargeResponse with StatusCode EVSE_Shutdown, to simulate a user-triggered session stop
                    msg = addV2GTPHeader("809a02180189551e24fc9e9160004100008182800000")
                if (testsuite_faultinjection_is_triggered(TC_EVSE_ResponseCode_Failed_for_PreChargeRes)):
                    # send a PreChargeResponse with ResponseCode Failed
                    msg = addV2GTPHeader("809a0125e6cecc516080408000008284de880800")
                self.addToTrace("responding " + prettyHexMessage(msg))
                self.showDecodedTransmitMessage(msg)
                self.publishStatus("PreCharging " + strPresentVoltage)
                if (not testsuite_faultinjection_is_triggered(TC_EVSE_Timeout_during_PreCharge)):
                    self.Tcp.transmit(msg)
                self.enterState(stateWaitForFlexibleRequest) # todo: not clear, what is specified in DIN
            if (strConverterResult.find("ContractAuthenticationReq")>0):
                # Ask the hardwareInterface, whether the user already presented a valid RFID or similar
                if (self.hardwareInterface.isUserAuthenticated()):
                    strAuthFinished = "1"
                    self.addToTrace("Contract is fine")
                else:
                    strAuthFinished = "0"
                    self.addToTrace("Contract is not (yet) fine")
                msg = addV2GTPHeader(exiEncode("EDl_" + strAuthFinished)) # EDl for Encode, Din, ContractAuthenticationResponse
                if (testsuite_faultinjection_is_triggered(TC_EVSE_ResponseCode_SequenceError_for_ContractAuthenticationRes)):
                    # send a ContractAuthenticationResponse with Responsecode SequenceError
                    msg = addV2GTPHeader("809a021a3b7c417774813310c0A200")
                self.addToTrace("responding " + prettyHexMessage(msg))
                self.showDecodedTransmitMessage(msg)
                self.publishStatus("ContractAuthentication")
                self.Tcp.transmit(msg)
                self.enterState(stateWaitForFlexibleRequest) # todo: not clear, what is specified in DIN
            if (strConverterResult.find("AuthorizationReq")>0):
                # Ask the hardwareInterface, whether the user already presented a valid RFID or similar
                if (self.hardwareInterface.isUserAuthenticated()):
                    strAuthFinished = "1"
                    self.addToTrace("User is Authorized")
                else:
                    strAuthFinished = "0"
                    self.addToTrace("User is not (yet) authorized")
                msg = addV2GTPHeader(exiEncode("E"+self.schemaSelection+"l_" + strAuthFinished)) # E1l for Encode, Iso1, AuthorizationResponse
                self.addToTrace("responding " + prettyHexMessage(msg))
                self.showDecodedTransmitMessage(msg)
                self.publishStatus("Authorization")
                self.Tcp.transmit(msg)
                self.enterState(stateWaitForFlexibleRequest)
            if (strConverterResult.find("CurrentDemandReq")>0):
                # check the request content, and fill response parameters
                uTarget = 220 # default in case we cannot decode the requested voltage
                iTarget = 1 # default...
                try:
                    jsondict = json.loads(strConverterResult)
                    strEVTargetVoltageValue = jsondict["EVTargetVoltage.Value"]
                    strEVTargetVoltageMultiplier = jsondict["EVTargetVoltage.Multiplier"]
                    uTarget = combineValueAndMultiplier(strEVTargetVoltageValue, strEVTargetVoltageMultiplier)
                    strEVTargetCurrentValue = jsondict["EVTargetCurrent.Value"]
                    strEVTargetCurrentMultiplier = jsondict["EVTargetCurrent.Multiplier"]
                    iTarget = combineValueAndMultiplier(strEVTargetCurrentValue, strEVTargetCurrentMultiplier)
                    self.addToTrace("EV wants EVTargetVoltage " + str(uTarget) + " and EVTargetCurrent " + str(iTarget))
                    current_soc = int(jsondict.get("DC_EVStatus.EVRESSSOC", -1))
                    full_soc = int(jsondict.get("FullSOC", -1))
                    energy_capacity = int(jsondict.get("EVEnergyCapacity.Value", -1))
                    energy_request = int(jsondict.get("EVEnergyRequest.Value", -1))
                    self.hardwareInterface.setPowerSupplyVoltageAndCurrent(uTarget, iTarget)

                    self.publishSoCs(current_soc, full_soc, energy_capacity, energy_request, origin="CurrentDemandReq")

                    self.callbackShowStatus(str(current_soc), "soc")
                    self.callbackShowStatus(str(uTarget) + "V, " + str(iTarget) + "A", "UandI")

                except:
                    self.addToTrace("ERROR: Could not decode the CurrentDemandReq")
                self.simulatedPresentVoltage = uTarget + 3*random() # The charger provides the voltage which is demanded by the car.
                strPresentVoltage = str(self.hardwareInterface.getInletVoltage()) #str(self.simulatedPresentVoltage)
                self.callbackShowStatus(strPresentVoltage, "EVSEPresentVoltage")
                strEVSEPresentCurrent = str(self.hardwareInterface.getAccuMaxCurrent()) #"1" # Just as a dummy current
                if (self.blChargeStopTrigger == 1 or self.hardwareInterface.stopRequest()):
                    # User pressed the STOP button on the charger. Send EVSE_Shutdown.
                    self.addToTrace("User pressed the STOP button on the charger. Sending EVSE_Shutdown.")
                    strEVSEStatus = "2" # 2=EVSE_Shutdown, means the user stopped the session on the charger.
                else:
                    # The normal case. No stop requested from user. Just send EVSE_Ready.
                    strEVSEStatus = "1" # 1=EVSE_Ready
                msg = addV2GTPHeader(exiEncode("E"+self.schemaSelection+"i_"+strPresentVoltage + "_" + strEVSEPresentCurrent + "_" + strEVSEStatus)) # EDi for Encode, Din, CurrentDemandRes
                if (testsuite_faultinjection_is_triggered(TC_EVSE_Malfunction_during_CurrentDemand)):
                    # send a CurrentDemandResponse with StatusCode EVSE_Malfunction, to simulate e.g. a voltage overshoot
                    msg = addV2GTPHeader("809a02203fa9e71c31bc920100821b430b933b4b7339032b93937b908e08043000081828440201818000040060a11c06030306402038441380")
                if (testsuite_faultinjection_is_triggered(TC_EVSE_Shutdown_during_CurrentDemand)):
                    # send a CurrentDemandResponse with StatusCode EVSE_Shutdown, to simulate a user stop request
                    msg = addV2GTPHeader("809a0125e15c2cd0e000410000018280001818000000040a1b648030300002038486580800")
                if (testsuite_faultinjection_is_triggered(TC_EVSE_ResponseCode_Failed_for_CurrentDemandRes)):
                    # send a CurrentDemandResponse with ResponseCode Failed
                    msg = addV2GTPHeader("809a0125e6cecc50e0804080000082867dc8081818000000040a1b64802030882702038486580800")
                self.addToTrace("responding " + prettyHexMessage(msg))
                self.showDecodedTransmitMessage(msg)
                self.publishStatus("CurrentDemand")
                if (not testsuite_faultinjection_is_triggered(TC_EVSE_Timeout_during_CurrentDemand)):
                    self.Tcp.transmit(msg)
                self.enterState(stateWaitForFlexibleRequest) # todo: not clear, what is specified in DIN
            if (strConverterResult.find("WeldingDetectionReq")>0):
                # todo: check the request content, and fill response parameters
                # simulate the decreasing voltage during the weldingDetection:
                self.simulatedPresentVoltage = self.simulatedPresentVoltage*0.8 + 3*random()
                strPresentVoltage = str(int(self.simulatedPresentVoltage*10)/10) # "345"
                self.callbackShowStatus(strPresentVoltage, "EVSEPresentVoltage")
                msg = addV2GTPHeader(exiEncode("E"+self.schemaSelection+"j_"+strPresentVoltage)) # EDj for Encode, Din, WeldingDetectionRes
                self.showDecodedTransmitMessage(msg)
                self.addToTrace("responding " + prettyHexMessage(msg))
                self.publishStatus("WeldingDetection")
                self.Tcp.transmit(msg)
                self.enterState(stateWaitForFlexibleRequest) # todo: not clear, what is specified in DIN
            if (strConverterResult.find("SessionStopReq")>0):
                # todo: check the request content, and fill response parameters
                msg = addV2GTPHeader(exiEncode("E"+self.schemaSelection+"k")) # EDk for Encode, Din, SessionStopRes
                self.showDecodedTransmitMessage(msg)
                self.addToTrace("responding " + prettyHexMessage(msg))
                self.publishStatus("SessionStop")
                self.Tcp.transmit(msg)
                self.enterState(stateWaitForFlexibleRequest) # todo: not clear, what is specified in DIN



        if (self.isTooLong()):
            self.enterState(0)

    def stateFunctionWaitForChargeParameterDiscoveryRequest(self):
        if (self.isTooLong()):
            self.enterState(0)

    def stateFunctionWaitForCableCheckRequest(self):
        if (self.isTooLong()):
            self.enterState(0)

    def stateFunctionWaitForPreChargeRequest(self):
        if (self.isTooLong()):
            self.enterState(0)

    def stateFunctionWaitForPowerDeliveryRequest(self):
        if (len(self.rxData)>0):
            self.addToTrace("In state WaitForPowerDeliveryRequest, received " + prettyHexMessage(self.rxData))
            self.addToTrace("Todo: Reaction in state WaitForPowerDeliveryRequest is not implemented yet.")
            self.rxData = []
            self.enterState(0)
        if (self.isTooLong()):
            self.enterState(0)


    stateFunctions = {
            stateWaitForSupportedApplicationProtocolRequest: stateFunctionWaitForSupportedApplicationProtocolRequest,
            stateWaitForSessionSetupRequest: stateFunctionWaitForSessionSetupRequest,
            stateWaitForServiceDiscoveryRequest: stateFunctionWaitForServiceDiscoveryRequest,
            stateWaitForServicePaymentSelectionRequest: stateFunctionWaitForServicePaymentSelectionRequest,
            stateWaitForFlexibleRequest: stateFunctionWaitForFlexibleRequest,
            stateWaitForChargeParameterDiscoveryRequest: stateFunctionWaitForChargeParameterDiscoveryRequest,
            stateWaitForCableCheckRequest: stateFunctionWaitForCableCheckRequest,
            stateWaitForPreChargeRequest: stateFunctionWaitForPreChargeRequest,
            stateWaitForPowerDeliveryRequest: stateFunctionWaitForPowerDeliveryRequest,
        }

    def reInit(self):
        self.addToTrace("re-initializing fsmEvse")
        self.state = 0
        self.cyclesInState = 0
        self.rxData = []
        self.simulatedPresentVoltage = 0
        self.Tcp.resetTheConnection()

    def socketStateNotification(self, notification):
        if (notification==0):
            # The TCP informs us, that the connection is broken.
            # Let's restart the state machine.
            self.publishStatus("TCP conn broken")
            self.addToTrace("re-initializing fsmEvse due to broken connection")
            self.reInit()
        if (notification==1):
            # The TCP informs us, that it is listening, means waiting for incoming connection.
            self.publishStatus("Listening TCP")
        if (notification==2):
            # The TCP informs us, that a connection is established.
            self.publishStatus("TCP connected")

    def __init__(self, addressManager, callbackAddToTrace, hardwareInterface, callbackShowStatus, callbackSoCStatus = None):
        self.callbackAddToTrace = callbackAddToTrace
        self.callbackShowStatus = callbackShowStatus
        self.callbackSoCStatus = callbackSoCStatus
        #todo self.addressManager = addressManager
        self.hardwareInterface = hardwareInterface
        self.addToTrace("initializing fsmEvse")
        self.faultInjectionDelayUntilSocketOpen_s = 0
        if (self.faultInjectionDelayUntilSocketOpen_s>0):
            self.addToTrace("Fault injection: waiting " + str(self.faultInjectionDelayUntilSocketOpen_s) + " s until opening the TCP socket.")
            time.sleep(self.faultInjectionDelayUntilSocketOpen_s)
        self.Tcp = pyPlcTcpSocket.pyPlcTcpServerSocket(self.callbackAddToTrace, self.socketStateNotification)
        self.state = 0
        self.cyclesInState = 0
        self.rxData = []
        self.evccid = ""
        self.blChargeStopTrigger = 0
        self.nCableCheckLoops = 0

    def mainfunction(self):
        self.Tcp.mainfunction() # call the lower-level worker
        if (self.Tcp.isRxDataAvailable()):
                self.rxData = self.Tcp.getRxData()
                #self.addToTrace("received " + str(self.rxData))
        # run the state machine:
        self.cyclesInState += 1 # for timeout handling, count how long we are in a state
        self.stateFunctions[self.state](self)

    def stopCharging(self):
        self.blChargeStopTrigger = 1


if __name__ == "__main__":
    print("Testing the evse state machine")
    evse = fsmEvse()
    print("Press Ctrl-Break for aborting")
    while (True):
        time.sleep(0.1)
        evse.mainfunction()


