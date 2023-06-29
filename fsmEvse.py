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

    def publishSoCs(self, current_soc: int, full_soc: int = -1, energy_capacity: int = -1, energy_request: int = -1, evccid: str = "", origin: str = ""):
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


    def stateFunctionWaitForSupportedApplicationProtocolRequest(self):
        if (len(self.rxData)>0):
            self.addToTrace("In state WaitForSupportedApplicationProtocolRequest, received " + prettyHexMessage(self.rxData))
            exidata = removeV2GTPHeader(self.rxData)
            self.rxData = []
            strConverterResult = exiDecode(exidata, "DH") # Decode Handshake-request
            self.addToTrace(strConverterResult)
            if (strConverterResult.find("supportedAppProtocolReq")>0):
                nDinSchemaID = 255 # invalid default value
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
                except:
                    self.addToTrace("ERROR: Could not decode the supportedAppProtocolReq")
                if (nDinSchemaID<255):
                    self.addToTrace("Detected DIN")
                    # TESTSUITE: When the EVSE received the Handshake, it selects a new test case.
                    testsuite_choose_testcase()
                    # Eh for encode handshake, SupportedApplicationProtocolResponse, with SchemaID as parameter
                    msg = addV2GTPHeader(exiEncode("Eh__"+str(nDinSchemaID)))
                    self.addToTrace("responding " + prettyHexMessage(msg))
                    self.Tcp.transmit(msg)
                    self.publishStatus("Schema negotiated")
                    self.enterState(stateWaitForSessionSetupRequest)
                else:
                    self.addToTrace("Error: The connected car does not support DIN. At the moment, the pyPLC only supports DIN.")

    def stateFunctionWaitForSessionSetupRequest(self):
        if (len(self.rxData)>0):
            self.simulatedPresentVoltage = 0
            self.addToTrace("In state WaitForSessionSetupRequest, received " + prettyHexMessage(self.rxData))
            exidata = removeV2GTPHeader(self.rxData)
            self.rxData = []
            strConverterResult = exiDecode(exidata, "DD")
            self.addToTrace(strConverterResult)
            if (strConverterResult.find("SessionSetupReq")>0):
                # todo: check the request content, and fill response parameters
                msg = addV2GTPHeader(exiEncode("EDa")) # EDa for Encode, Din, SessionSetupResponse
                self.addToTrace("responding " + prettyHexMessage(msg))
                if (testsuite_faultinjection_is_triggered(TC_EVSE_ResponseCode_SequenceError_for_SessionSetup)):
                    # send a SessionSetupResponse with Responsecode SequenceError
                    msg = addV2GTPHeader("809a0232417b661514a4cb91e0A02d0691559529548c0841e0fc1af4507460c0")
                self.addToTrace("responding " + prettyHexMessage(msg))
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
            strConverterResult = exiDecode(exidata, "DD")
            self.addToTrace(strConverterResult)
            if (strConverterResult.find("ServiceDiscoveryReq")>0):
                # todo: check the request content, and fill response parameters
                msg = addV2GTPHeader(exiEncode("EDb")) # EDb for Encode, Din, ServiceDiscoveryResponse
                if (testsuite_faultinjection_is_triggered(TC_EVSE_ResponseCode_SequenceError_for_ServiceDiscoveryRes)):
                    # send a ServiceDiscoveryRes with Responsecode SequenceError
                    msg = addV2GTPHeader("809a021a3b7c417774813311a0A120024100c4")
                self.addToTrace("responding " + prettyHexMessage(msg))
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
            strConverterResult = exiDecode(exidata, "DD")
            self.addToTrace(strConverterResult)
            if (strConverterResult.find("ServicePaymentSelectionReq")>0):
                # todo: check the request content, and fill response parameters
                msg = addV2GTPHeader(exiEncode("EDc")) # EDc for Encode, Din, ServicePaymentSelectionResponse
                if (testsuite_faultinjection_is_triggered(TC_EVSE_ResponseCode_SequenceError_for_ServicePaymentSelectionRes)):
                    # send a ServicePaymentSelectionRes with Responsecode SequenceError
                    msg = addV2GTPHeader("809a021a3b7c417774813311c0A0")
                self.addToTrace("responding " + prettyHexMessage(msg))
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
            strConverterResult = exiDecode(exidata, "DD")
            self.addToTrace(strConverterResult)
            if (strConverterResult.find("PowerDeliveryReq")>0):
                # todo: check the request content, and fill response parameters
                self.addToTrace("Received PowerDeliveryReq. Extracting SoC parameters")
                jsondict = json.loads(strConverterResult)
                current_soc = int(jsondict.get("EVRESSSOC", -1))
                self.publishSoCs(current_soc, origin="PowerDeliveryReq")
                msg = addV2GTPHeader(exiEncode("EDh")) # EDh for Encode, Din, PowerDeliveryResponse
                if (testsuite_faultinjection_is_triggered(TC_EVSE_ResponseCode_Failed_for_PowerDeliveryRes)):
                    # send a PowerDeliveryResponse with Responsecode Failed
                    msg = addV2GTPHeader("809a0125e6cecc51408420400000")
                self.addToTrace("responding " + prettyHexMessage(msg))
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
                msg = addV2GTPHeader(exiEncode("EDe")) # EDe for Encode, Din, ChargeParameterDiscoveryResponse
                if (testsuite_faultinjection_is_triggered(TC_EVSE_ResponseCode_ServiceSelectionInvalid_for_ChargeParameterDiscovery)):
                    # send a ChargeParameterDiscoveryResponse with Responsecode ServiceSelectionInvalid
                    msg = addV2GTPHeader("809a0125e6cecd50810001ec00201004051828758405500080000101844138101c2432c04081436c900c0c000041435ecc044606000200")
                self.addToTrace("responding " + prettyHexMessage(msg))
                self.publishStatus("ChargeParamDiscovery")
                self.Tcp.transmit(msg)
                self.enterState(stateWaitForFlexibleRequest) # todo: not clear, what is specified in DIN
            if (strConverterResult.find("CableCheckReq")>0):
                # todo: check the request content, and fill response parameters
                # todo: make a real cable check, and while it is ongoing, send "Ongoing".
                self.addToTrace("Received CableCheckReq. Extracting SoC parameters via DC")
                jsondict = json.loads(strConverterResult)
                current_soc = int(jsondict.get("DC_EVStatus.EVRESSSOC", -1))
                self.publishSoCs(current_soc, -1, -1, origin="CableCheckReq")

                msg = addV2GTPHeader(exiEncode("EDf")) # EDf for Encode, Din, CableCheckResponse
                if (testsuite_faultinjection_is_triggered(TC_EVSE_ResponseCode_Failed_for_CableCheckRes)):
                    # send a CableCheckResponse with Responsecode Failed
                    msg = addV2GTPHeader("809a0125e6cecc5020804080000400")
                self.addToTrace("responding " + prettyHexMessage(msg))
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
                strPresentVoltage = str(self.simulatedPresentVoltage) # "345"
                self.callbackShowStatus(strPresentVoltage, "EVSEPresentVoltage")
                msg = addV2GTPHeader(exiEncode("EDg_"+strPresentVoltage)) # EDg for Encode, Din, PreChargeResponse
                if (testsuite_faultinjection_is_triggered(TC_EVSE_Shutdown_during_PreCharge)):
                    # send a PreChargeResponse with StatusCode EVSE_Shutdown, to simulate a user-triggered session stop
                    msg = addV2GTPHeader("809a02180189551e24fc9e9160004100008182800000")
                if (testsuite_faultinjection_is_triggered(TC_EVSE_ResponseCode_Failed_for_PreChargeRes)):
                    # send a PreChargeResponse with ResponseCode Failed
                    msg = addV2GTPHeader("809a0125e6cecc516080408000008284de880800")
                self.addToTrace("responding " + prettyHexMessage(msg))
                self.publishStatus("PreCharging " + strPresentVoltage)
                if (not testsuite_faultinjection_is_triggered(TC_EVSE_Timeout_during_PreCharge)):
                    self.Tcp.transmit(msg)
                self.enterState(stateWaitForFlexibleRequest) # todo: not clear, what is specified in DIN
            if (strConverterResult.find("ContractAuthenticationReq")>0):
                # todo: check the request content, and fill response parameters
                msg = addV2GTPHeader(exiEncode("EDl")) # EDl for Encode, Din, ContractAuthenticationResponse
                if (testsuite_faultinjection_is_triggered(TC_EVSE_ResponseCode_SequenceError_for_ContractAuthenticationRes)):
                    # send a ContractAuthenticationResponse with Responsecode SequenceError
                    msg = addV2GTPHeader("809a021a3b7c417774813310c0A200")
                self.addToTrace("responding " + prettyHexMessage(msg))
                self.publishStatus("ContractAuthentication")
                self.Tcp.transmit(msg)
                self.enterState(stateWaitForFlexibleRequest) # todo: not clear, what is specified in DIN
            if (strConverterResult.find("CurrentDemandReq")>0):
                # check the request content, and fill response parameters
                uTarget = 220 # default in case we cannot decode the requested voltage
                try:
                    jsondict = json.loads(strConverterResult)
                    strEVTargetVoltageValue = jsondict["EVTargetVoltage.Value"]
                    strEVTargetVoltageMultiplier = jsondict["EVTargetVoltage.Multiplier"]
                    uTarget = combineValueAndMultiplier(strEVTargetVoltageValue, strEVTargetVoltageMultiplier)
                    self.addToTrace("EV wants EVTargetVoltage " + str(uTarget))
                    current_soc = int(jsondict.get("DC_EVStatus.EVRESSSOC", -1))
                    full_soc = int(jsondict.get("FullSOC", -1))
                    energy_capacity = int(jsondict.get("EVEnergyCapacity.Value", -1))
                    energy_request = int(jsondict.get("EVEnergyRequest.Value", -1))

                    self.publishSoCs(current_soc, full_soc, energy_capacity, energy_request, origin="CurrentDemandReq")

                    self.callbackShowStatus(str(current_soc), "soc")

                except:
                    self.addToTrace("ERROR: Could not decode the CurrentDemandReq")
                self.simulatedPresentVoltage = uTarget + 3*random() # The charger provides the voltage which is demanded by the car.
                strPresentVoltage = str(self.simulatedPresentVoltage)
                self.callbackShowStatus(strPresentVoltage, "EVSEPresentVoltage")
                strEVSEPresentCurrent = "1" # Just as a dummy current
                msg = addV2GTPHeader(exiEncode("EDi_"+strPresentVoltage + "_" + strEVSEPresentCurrent)) # EDi for Encode, Din, CurrentDemandRes
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
                self.publishStatus("CurrentDemand")
                if (not testsuite_faultinjection_is_triggered(TC_EVSE_Timeout_during_CurrentDemand)):
                    self.Tcp.transmit(msg)
                self.enterState(stateWaitForFlexibleRequest) # todo: not clear, what is specified in DIN
            if (strConverterResult.find("WeldingDetectionReq")>0):
                # todo: check the request content, and fill response parameters
                msg = addV2GTPHeader(exiEncode("EDj")) # EDj for Encode, Din, WeldingDetectionRes
                self.addToTrace("responding " + prettyHexMessage(msg))
                self.publishStatus("WeldingDetection")
                self.Tcp.transmit(msg)
                self.enterState(stateWaitForFlexibleRequest) # todo: not clear, what is specified in DIN
            if (strConverterResult.find("SessionStopReq")>0):
                # todo: check the request content, and fill response parameters
                msg = addV2GTPHeader(exiEncode("EDk")) # EDk for Encode, Din, SessionStopRes
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
        #todo self.hardwareInterface = hardwareInterface
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

    def mainfunction(self):
        self.Tcp.mainfunction() # call the lower-level worker
        if (self.Tcp.isRxDataAvailable()):
                self.rxData = self.Tcp.getRxData()
                #self.addToTrace("received " + str(self.rxData))
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


