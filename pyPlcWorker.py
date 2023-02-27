# Worker for the pyPLC
#
# Tested on
#   - Windows10 with python 3.9 and
#   - Raspbian with python 3.9
#

#------------------------------------------------------------
import pyPlcHomeplug
import fsmEvse
import fsmPev
from pyPlcModes import *
import addressManager
import time
import subprocess
import hardwareInterface
        

class pyPlcWorker():
    def __init__(self, callbackAddToTrace=None, callbackShowStatus=None, mode=C_EVSE_MODE, isSimulationMode=0):
        print("initializing pyPlcWorker") 
        self.nMainFunctionCalls=0
        self.mode = mode
        self.strUserAction = ""
        self.addressManager = addressManager.addressManager()
        self.addressManager.findLinkLocalIpv6Address()
        self.callbackAddToTrace = callbackAddToTrace
        self.callbackShowStatus = callbackShowStatus
        self.oldAvlnStatus = 0
        self.isSimulationMode = isSimulationMode
        self.hp = pyPlcHomeplug.pyPlcHomeplug(self.workerAddToTrace, self.showStatus, self.mode, self.addressManager, self.callbackReadyForTcp, self.isSimulationMode)
        self.hardwareInterface = hardwareInterface.hardwareInterface(self.workerAddToTrace, self.showStatus)
        self.hp.printToUdp("pyPlcWorker init")
        # Find out the version number, using git.
        # see https://stackoverflow.com/questions/14989858/get-the-current-git-hash-in-a-python-script
        try:
            strLabel = str(subprocess.check_output(["git", "describe", "--tags"], text=True).strip())
        except:
            strLabel = "(unknown version. 'git describe --tags' failed.)"
        self.workerAddToTrace("[pyPlcWorker] Software version " + strLabel)  
        if (self.mode == C_EVSE_MODE):
            self.evse = fsmEvse.fsmEvse(self.addressManager, self.workerAddToTrace, self.hardwareInterface, self.showStatus)
        if (self.mode == C_PEV_MODE):
            self.pev = fsmPev.fsmPev(self.addressManager, self.workerAddToTrace, self.hardwareInterface, self.showStatus)
    def __del__(self):
        if (self.mode == C_PEV_MODE):
            print("worker: deleting pev")
            del(self.pev)
        
    def workerAddToTrace(self, s):
        # The central logging function. All logging messages from the different parts of the project
        # shall come here.
        #print("workerAddToTrace " + s)
        self.callbackAddToTrace(s) # give the message to the upper level, eg for console log.
        self.hp.printToUdp(s) # give the message to the udp for remote logging.
        
    def showStatus(self, s, selection = "", strAuxInfo1="", strAuxInfo2=""):
        self.callbackShowStatus(s, selection)
        if (selection == "pevState"):
            self.hardwareInterface.showOnDisplay(s, strAuxInfo1, strAuxInfo2)

    def callbackReadyForTcp(self, status):
        if (status==1):
            self.workerAddToTrace("[PLCWORKER] Network is established, ready for TCP.")
            #self.workerAddToTrace("[PLCWORKER] Waiting....")            
            #time.sleep(5)
            #self.workerAddToTrace("[PLCWORKER] now...")            
            if (self.oldAvlnStatus==0):
                self.oldAvlnStatus = 1
                if (self.mode == C_PEV_MODE):
                    self.pev.reInit()
                    
        else:
            self.workerAddToTrace("[PLCWORKER] no network")
            self.oldAvlnStatus = 0
        
    def mainfunction(self):
        self.nMainFunctionCalls+=1
        #self.showStatus("pyPlcWorker loop " + str(self.nMainFunctionCalls))
        self.hp.mainfunction() # call the lower-level workers
        self.hardwareInterface.mainfunction()
        if (self.mode == C_EVSE_MODE):
            self.evse.mainfunction() # call the evse state machine
        if (self.mode == C_PEV_MODE):
            self.pev.mainfunction() # call the pev state machine
        
    def handleUserAction(self, strAction):
        self.strUserAction = strAction
        print("user action " + strAction)
        if (strAction == "P"):
            print("switching to PEV mode")
            self.mode = C_PEV_MODE
            if (hasattr(self, 'evse')):
                print("deleting evse")
                del self.evse
            self.hp.enterPevMode()
            if (not hasattr(self, 'pev')):
                print("creating pev")
                self.pev = fsmPev.fsmPev(self.addressManager, self.workerAddToTrace, self.hardwareInterface, self.callbackShowStatus)
            self.pev.reInit()
        if (strAction == "E"):
            print("switching to EVSE mode")
            self.mode = C_EVSE_MODE
            if (hasattr(self, 'pev')):
                print("deleting pev")
                del self.pev
            self.hp.enterEvseMode()
            if (not hasattr(self, 'evse')):
                print("creating fsmEvse")
                self.evse = fsmEvse.fsmEvse(self.workerAddToTrace)
            self.evse.reInit()
        if (strAction == "L"):
            print("switching to LISTEN mode")
            self.mode = C_LISTEN_MODE
            self.hp.enterListenMode()  
            if (hasattr(self, 'evse')):
                print("deleting evse")
                del self.evse
            if (hasattr(self, 'pev')):
                print("deleting pev")
                del self.pev
        if (strAction == "space"):
            print("stopping the charge process")
            if (hasattr(self, 'pev')):
                self.pev.stopCharging()
        # self.addToTrace("UserAction " + strAction)
        self.hp.sendTestFrame(strAction)

