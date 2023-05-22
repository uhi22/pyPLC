
# For testing.
#
# Concept: This module allows to trigger abnormal situations, to test the reaction of the software ("fault insertion testing").
# In the place in the software, where the fault shall be injected, add a condition like
#     if (testsuite_faultinjection_is_triggered(TC_MY_TESTCASE_FOR_SOMETHING)):
#         DoSomethingStrange()
# In normal software run, this condition is never fulfilled and does not disturb. If the related test case is activated,
# by setting testsuite_testcase_number = TC_MY_TESTCASE_FOR_SOMETHING below, the condition will fire and the fault is injected.
# A number of delay cycles can be configured with testsuite_delayCycles below.
#
# Detailled docu see doc/testing_and_simulation.md


from udplog import udplog_log
from configmodule import getConfigValue, getConfigValueBool


# The list of test cases. Each must have a unique test case ID.
TC_NOTHING_TO_TEST = 0
TC_EVSE_ResponseCode_SequenceError_for_SessionSetup = 1
TC_EVSE_ResponseCode_Failed_for_CableCheckRes = 2
TC_EVSE_ResponseCode_SequenceError_for_ServiceDiscoveryRes = 3
TC_EVSE_ResponseCode_SequenceError_for_ServicePaymentSelectionRes = 4
TC_EVSE_ResponseCode_SequenceError_for_ContractAuthenticationRes = 5
TC_EVSE_ResponseCode_ServiceSelectionInvalid_for_ChargeParameterDiscovery = 6
TC_EVSE_ResponseCode_Failed_for_PreChargeRes = 7
TC_EVSE_ResponseCode_Failed_for_PowerDeliveryRes = 8
TC_EVSE_ResponseCode_Failed_for_CurrentDemandRes = 9
TC_EVSE_Timeout_during_CableCheck = 10
TC_EVSE_Timeout_during_PreCharge = 11
TC_EVSE_Shutdown_during_PreCharge = 12
TC_EVSE_Shutdown_during_CurrentDemand = 13
TC_EVSE_Malfunction_during_CurrentDemand = 14
TC_EVSE_Timeout_during_CurrentDemand = 15
TC_EVSE_GoodCase = 16
TC_EVSE_LastTest = 17


# variables
testsuite_testcase_number = 0
testsuite_delayCycles = 0
testsuite_TcTitle = "(title not initialized)"

# Counter variable for delaying the trigger
testsuite_counter = 0

def testsuite_printToTestLog(s):
 fileOut = open('testresults.txt', 'a') # open the result file for appending
 print(s, file=fileOut)
 fileOut.close()

def testsuite_getTcNumber():
    if (testsuite_testcase_number==0):
        return "(no tests)"
    else:
        return str(testsuite_testcase_number) + testsuite_TcTitle

def testsuite_faultinjection_is_triggered(context):
    global testsuite_counter, testsuite_testcase_number, testsuite_delayCycles
    isTestcaseFired = False
    if (context==testsuite_testcase_number): # if the call context is matching the intended test case
        testsuite_counter += 1 # count the number of matching calls
        isTestcaseFired = testsuite_counter>=testsuite_delayCycles # and fire the test case if the intended number is reached
        if (isTestcaseFired):
            print("[TESTSUITE] Fired test case " + str(context) + " TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT")
            s = "[TESTSUITE] Fired test case " + str(context)
            udplog_log(s, "testsuite")
    return isTestcaseFired


def testsuite_choose_testcase():
    global testsuite_counter, testsuite_testcase_number, testsuite_delayCycles
    global testsuite_observedResult
    global testsuite_expectedResult
    global testsuite_TcTitle
    
    if (not getConfigValueBool("testsuite_enable")):
        testsuite_testcase_number = TC_NOTHING_TO_TEST
        return
    
    try:
        if (testsuite_expectedResult is None):
            testsuite_expectedResult = ""
    except:
        testsuite_expectedResult = ""
        
    # as first step, before choosing the next test case, check the result of the ongoing test case
    if (testsuite_expectedResult!=""):
        s = "ExpectedResult: " + testsuite_expectedResult
        s = s + ", ObservedResult: " + testsuite_observedResult
        if (testsuite_expectedResult!=testsuite_observedResult):
            s = "FAIL " + s
        else:
            s = "PASS " + s
        print(s)
        udplog_log(s, "testsuite")
        x = "Result for Testcase " + str(testsuite_testcase_number) + " " + testsuite_TcTitle
        testsuite_printToTestLog(x)
        testsuite_printToTestLog(s)
    if (testsuite_testcase_number<TC_EVSE_LastTest):
        testsuite_testcase_number+=1
        print("[TESTSUITE] Setting up test case " + str(testsuite_testcase_number) + " TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT")
        s = "[TESTSUITE] Setting up test case " + str(testsuite_testcase_number)
        udplog_log(s, "testsuite")
        testsuite_counter = 0
        testsuite_delayCycles = 5 # just a default
        testsuite_expectedResult = "" # just a default
        testsuite_observedResult = "" # just a default
        testsuite_TcTitle = "(title missing)" # just a default
        
        # For each test case, configure the test parameters and the expected result
        if (testsuite_testcase_number == TC_EVSE_Timeout_during_CableCheck):
            testsuite_delayCycles=0 # immediately timeout
            testsuite_expectedResult = "TSRS_SafeShutdownFinished"
            testsuite_TcTitle = "Timeout during CableCheck shall lead to SafeShutdown"

        if (testsuite_testcase_number == TC_EVSE_Timeout_during_PreCharge):
            testsuite_delayCycles=0 # immediately timeout
            testsuite_expectedResult = "TSRS_SafeShutdownFinished"
            testsuite_TcTitle = "Timeout during PreCharge shall lead to SafeShutdown"

        if (testsuite_testcase_number == TC_EVSE_Shutdown_during_PreCharge):
            testsuite_delayCycles=2 # shutdown after 2 ok-cycles
            testsuite_expectedResult = "TSRS_SafeShutdownFinished"
            testsuite_TcTitle = "Shutdown during PreCharge shall lead to SafeShutdown"
            
        if (testsuite_testcase_number == TC_EVSE_Shutdown_during_CurrentDemand):
            testsuite_delayCycles=20 # shutdown after 20 ok-cycles
            testsuite_expectedResult = "TSRS_SafeShutdownFinished"
            testsuite_TcTitle = "Shutdown during CurrentDemand shall lead to SafeShutdown"
            
        if (testsuite_testcase_number == TC_EVSE_Malfunction_during_CurrentDemand):
            testsuite_delayCycles=5 # malfunction after 5 ok-cycles
            testsuite_expectedResult = "TSRS_SafeShutdownFinished"
            testsuite_TcTitle = "Malfunction during CurrentDemand shall lead to SafeShutdown"
            
        if (testsuite_testcase_number == TC_EVSE_Timeout_during_CurrentDemand):
            testsuite_delayCycles=30 # timeout after 30 ok-cycles
            testsuite_expectedResult = "TSRS_SafeShutdownFinished"
            testsuite_TcTitle = "Timeout during CurrentDemand shall lead to SafeShutdown"
            
        if (testsuite_testcase_number == TC_EVSE_ResponseCode_SequenceError_for_SessionSetup):
            testsuite_delayCycles=0 # immediately
            testsuite_expectedResult = "TSRS_SafeShutdownFinished"
            testsuite_TcTitle = "SequenceError in SessionSetup shall lead to SafeShutdown"
        if (testsuite_testcase_number == TC_EVSE_ResponseCode_SequenceError_for_ServiceDiscoveryRes):
            testsuite_delayCycles=0 # immediately
            testsuite_expectedResult = "TSRS_SafeShutdownFinished"
            testsuite_TcTitle = "SequenceError in ServiceDiscoveryRes shall lead to SafeShutdown"
        if (testsuite_testcase_number == TC_EVSE_ResponseCode_SequenceError_for_ServicePaymentSelectionRes):
            testsuite_delayCycles=0 # immediately
            testsuite_expectedResult = "TSRS_SafeShutdownFinished"
            testsuite_TcTitle = "SequenceError in ServicePaymentSelectionRes shall lead to SafeShutdown"
        if (testsuite_testcase_number == TC_EVSE_ResponseCode_SequenceError_for_ContractAuthenticationRes):
            testsuite_delayCycles=0 # immediately
            testsuite_expectedResult = "TSRS_SafeShutdownFinished"
            testsuite_TcTitle = "SequenceError in ContractAuthenticationRes shall lead to SafeShutdown"
        if (testsuite_testcase_number == TC_EVSE_ResponseCode_ServiceSelectionInvalid_for_ChargeParameterDiscovery):
            testsuite_delayCycles=0 # immediately
            testsuite_expectedResult = "TSRS_SafeShutdownFinished"
            testsuite_TcTitle = "ServiceSelectionInvalid in ChargeParameterDiscoveryshall lead to SafeShutdown"
        
        if (testsuite_testcase_number == TC_EVSE_ResponseCode_Failed_for_CableCheckRes):
            testsuite_delayCycles=0 # immediately in the first message
            testsuite_expectedResult = "TSRS_SafeShutdownFinished"
            testsuite_TcTitle = "Failed in CableCheckRes shall lead to SafeShutdown"
            
        if (testsuite_testcase_number == TC_EVSE_ResponseCode_Failed_for_PreChargeRes):
            testsuite_delayCycles=2 # after two ok cycles, we inject the fault in the third cycle
            testsuite_expectedResult = "TSRS_SafeShutdownFinished"
            testsuite_TcTitle = "Failed in PreChargeRes shall lead to SafeShutdown"
            
        if (testsuite_testcase_number == TC_EVSE_ResponseCode_Failed_for_PowerDeliveryRes):
            testsuite_delayCycles=0 # immediately
            testsuite_expectedResult = "TSRS_SafeShutdownFinished"
            testsuite_TcTitle = "Failed in PowerDeliveryRes shall lead to SafeShutdown"
            
        if (testsuite_testcase_number == TC_EVSE_ResponseCode_Failed_for_CurrentDemandRes):
            testsuite_delayCycles=10 # fire the fault after 10 ok-cycles
            testsuite_expectedResult = "TSRS_SafeShutdownFinished"
            testsuite_TcTitle = "Failed in CurrentDemandRes shall lead to SafeShutdown"
            
        if (testsuite_testcase_number == TC_EVSE_GoodCase):
            # Test case for the good case: Normal charging, no errors.
            testsuite_delayCycles=0 # not relevant
            testsuite_expectedResult = "TSRS_ChargingFinished"
            testsuite_TcTitle = "Good case, normal charging without errors"
            
        

def testsuite_reportstatus(s):
    # give the test status to the UDP, to inform the other side and to have it in the network log.
    udplog_log(s, "testsuite")
    pass
    

def testsuite_evaluateIpv4Packet(pkt):
    # The testsuite listens to syslog messages which are coming from the other side,
    # to know what is going on.
    global testsuite_observedResult
    if (len(pkt)>50):
        protocol = pkt[23]
        destinationport = pkt[36]*256 + pkt[37]
        if ((protocol == 0x11) and (destinationport==0x0202)): # it is an UDP packet to the syslog port
            baSyslog = pkt[46:]
            strSyslog = ""
            syslogLen = len(baSyslog)
            if (syslogLen>100):
                syslogLen=100
            for i in range(0, syslogLen-1): # one less, remove the trailing 0x00
                x = baSyslog[i]
                if (x<0x20):
                    x=0x20 # make unprintable character to space.
                strSyslog+=chr(x) # convert ASCII code to string
            print("[Testsuite]  received syslog packet: " + strSyslog)
            if (strSyslog[0:5]=="TSRS_"):
                # it is a TestSuiteReportStatus message.
                testsuite_observedResult = strSyslog

if __name__ == "__main__":
    print("Testing the mytestsuite")
    print("nothing to do")
