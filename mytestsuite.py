
# For testing.
#
# Concept: This module allows to trigger abnormal situations, to test the reaction of the software ("fault insertion testing").
# In the place in the software, where the fault shall be injected, add a condition like
#     if (testsuite_faultinjection_is_triggered(TC_MY_TESTCASE_FOR_SOMETHING)):
#         DoSomethingStrange()
# In normal software run, this condition is never fulfilled and does not disturb. If the related test case is activated,
# by setting testsuite_testcase_number = TC_MY_TESTCASE_FOR_SOMETHING below, the condition will fire and the fault is injected.
# A number of delay cycles can be configured with testsuite_delayCycles below.

# The list of test cases. Each must have a unique test case ID.
TC_NOTHING_TO_TEST = 0
TC_EVSE_Shutdown_during_PreCharge = 1000
TC_EVSE_Shutdown_during_CurrentDemand = 2000
TC_EVSE_Malfunction_during_CurrentDemand = 2001

# Here we configure, which test case should fire, and after which number of calls:
testsuite_testcase_number = TC_EVSE_Malfunction_during_CurrentDemand
testsuite_delayCycles = 5



# Counter variable for delaying the trigger
testsuite_counter = 0

def testsuite_faultinjection_is_triggered(context):
    global testsuite_counter, testsuite_testcase_number, testsuite_delayCycles
    isTestcaseFired = False
    if (context==testsuite_testcase_number): # if the call context is matching the intended test case
        testsuite_counter += 1 # count the number of matching calls
        isTestcaseFired = testsuite_counter>=testsuite_delayCycles # and fire the test case if the intended number is reached
        if (isTestcaseFired):
            print("[TESTSUITE] Fired test case " + str(context) + " TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT")
    return isTestcaseFired


if __name__ == "__main__":
    print("Testing the mytestsuite")
    print("nothing to do")
