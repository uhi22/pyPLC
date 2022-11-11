# Worker for the pyPLC
#
# Tested on Windows10 with python 3.9
#

#------------------------------------------------------------
import pyPlcHomeplug
import fsmEvse
import fsmPev
from pyPlcModes import *
import addressManager
        

class pyPlcWorker():
    def __init__(self, callbackAddToTrace=None, callbackShowStatus=None, mode=C_EVSE_MODE):
        print("initializing pyPlcWorker") 
        self.nMainFunctionCalls=0
        self.mode = mode
        self.strUserAction = ""
        self.addressManager = addressManager.addressManager()
        self.addressManager.findLinkLocalIpv6Address()
        self.callbackAddToTrace = callbackAddToTrace
        self.callbackShowStatus = callbackShowStatus
        self.hp = pyPlcHomeplug.pyPlcHomeplug(self.callbackAddToTrace, self.callbackShowStatus, self.mode, self.addressManager)
        if (self.mode == C_EVSE_MODE):
            self.evse = fsmEvse.fsmEvse()
        if (self.mode == C_PEV_MODE):
            self.pev = fsmPev.fsmPev()
 
    def addToTrace(self, s):
        self.callbackAddToTrace(s)
        
    def showStatus(self, s, selection = ""):
        self.callbackShowStatus(s, selection)        
        
    def mainfunction(self):
        self.nMainFunctionCalls+=1
        #self.showStatus("pyPlcWorker loop " + str(self.nMainFunctionCalls))
        self.hp.mainfunction() # call the lower-level worker
        if (self.mode == C_EVSE_MODE):
            self.evse.mainfunction() # call the evse state machine
        if (self.mode == C_PEV_MODE):
            self.pev.mainfunction() # call the pev state machine
        
    def handleUserAction(self, strAction):
        self.strUserAction = strAction
        if (strAction == "P"):
            print("switching to PEV mode")
            self.mode = C_PEV_MODE
            if (hasattr(self, 'evse')):
                print("deleting evse")
                del self.evse
            self.hp.enterPevMode()
            if (not hasattr(self, 'pev')):
                print("creating pev")
                self.pev = fsmPev.fsmPev()
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
                self.evse = fsmEvse.fsmEvse()
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
        # self.addToTrace("UserAction " + strAction)
        self.hp.sendTestFrame(strAction)

