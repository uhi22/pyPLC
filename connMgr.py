


# Connection Manager

# This module is informed by the several state machines in case of good connection.
#   It calculates an overall ConnectionLevel.
#   This ConnectionLevel is provided to the state machines, so that each state machine
#   has the possiblity to decide whether it needs to do something or just stays silent.
#   
#   The basic rule is, that a good connection on higher layer (e.g. TCP) implicitely
#   confirms the good connection on lower layer (e.g. Modem presence). This means,
#   the lower-layer state machine can stay silent as long as the upper layers are working
#   fine.

from configmodule import getConfigValue, getConfigValueBool
import sys # For exit_on_session_end hack

CONNLEVEL_100_APPL_RUNNING = 100
CONNLEVEL_80_TCP_RUNNING = 80
CONNLEVEL_50_SDP_DONE = 50
CONNLEVEL_20_TWO_MODEMS_FOUND = 20
CONNLEVEL_15_SLAC_ONGOING = 15
CONNLEVEL_10_ONE_MODEM_FOUND = 10
CONNLEVEL_5_ETH_LINK_PRESENT = 5

CONNMGR_CYCLES_PER_SECOND = 33 # 33 cycles for one second, is 30ms call cycle
CONNMGR_TIMER_MAX = (5*33) # 5 seconds until an OkReport is forgotten.
CONNMGR_TIMER_MAX_10s = (10*33) # 10 seconds until an OkReport is forgotten.
CONNMGR_TIMER_MAX_15s = (15*33) # 15 seconds until an OkReport is forgotten.
CONNMGR_TIMER_MAX_20s = (20*33) # 20 seconds until an OkReport is forgotten.


class connMgr():
    def getConnectionLevel(self):
        return self.ConnectionLevel

    def printDebugInfos(self):
        s = "[CONNMGR] " + str(self.timerEthLink) + " " \
                     + str(self.timerModemLocal) + " " \
                     + str(self.timerModemRemote) + " " \
                     + str(self.timerSlac) + " " \
                     + str(self.timerSDP) + " " \
                     + str(self.timerTCP) + " " \
                     + str(self.timerAppl) + " " \
                     + " --> " + str(self.ConnectionLevel)
        self.addToTrace(s)


    def __init__(self, callbackAddToTrace, callbackShowStatus):
        self.timerEthLink = 0
        self.timerModemLocal = 0
        self.timerModemRemote = 0
        self.timerSlac = 0
        self.timerSDP = 0
        self.timerTCP = 0
        self.timerAppl = 0
        self.ConnectionLevel = 0
        self.ConnectionLevelOld = 0
        self.cycles = 0
        self.addToTrace = callbackAddToTrace
        
    def mainfunction(self):
        # shortcut: we do not check the ethernet link, instead, we assume it is just always present.
        self.timerEthLink = 10
        # count all the timers down
        if (self.timerEthLink>0):
            self.timerEthLink-=1
        if (self.timerModemLocal>0):
            self.timerModemLocal-=1
        if (self.timerModemRemote>0):
            self.timerModemRemote-=1
        if (self.timerSlac>0):
            self.timerSlac-=1
        if (self.timerSDP>0):
            self.timerSDP-=1
        if (self.timerTCP>0):
            self.timerTCP-=1
        if (self.timerAppl>0):
            self.timerAppl-=1
        # Based on the timers, calculate the connectionLevel.
        if (self.timerAppl>0):
            self.ConnectionLevel=CONNLEVEL_100_APPL_RUNNING
        else:
            if (self.timerTCP>0):
                self.ConnectionLevel=CONNLEVEL_80_TCP_RUNNING
            else:
                if (self.timerSDP>0):
                    self.ConnectionLevel=CONNLEVEL_50_SDP_DONE
                else:
                    if (self.timerModemRemote>0):
                        self.ConnectionLevel=CONNLEVEL_20_TWO_MODEMS_FOUND
                    else:
                        if (self.timerSlac>0):
                            self.ConnectionLevel=CONNLEVEL_15_SLAC_ONGOING
                        else:
                            if (self.timerModemLocal>0):
                                self.ConnectionLevel=CONNLEVEL_10_ONE_MODEM_FOUND
                            else:
                                if (self.timerEthLink>0):
                                    self.ConnectionLevel=CONNLEVEL_5_ETH_LINK_PRESENT
                                else:
                                    self.ConnectionLevel=0
        if (self.ConnectionLevelOld!=self.ConnectionLevel):
            self.addToTrace("[CONNMGR] ConnectionLevel changed from " + str(self.ConnectionLevelOld) + " to " + str(self.ConnectionLevel))
            if ((self.ConnectionLevelOld==100) and (self.ConnectionLevel<100)):
                # We had a charging session, and now it is gone.
                # Depending on configuration option, we may end the script here.
                if getConfigValueBool("exit_on_session_end"):
                    # TODO: This is a hack. Do this in fsmPev instead?
                    self.addToTrace("[CONNMGR] Terminating the application.")
                    sys.exit(0)

            self.ConnectionLevelOld = self.ConnectionLevel
        if ((self.cycles % 33)==0):
            # once per second
            self.printDebugInfos()
        self.cycles+=1

    def ModemFinderOk(self, numberOfFoundModems):
        if (numberOfFoundModems>=1):
            self.timerModemLocal = CONNMGR_TIMER_MAX
        if (numberOfFoundModems>=2):
            self.timerModemRemote = CONNMGR_TIMER_MAX_10s # 10s for the slac sequence, to avoid too fast timeout

    def SlacOk(self):
        # The SetKey was sent to the local modem. This leads to restart of the
        # local modem, and potenially also for the remote modem. If both modems are up,
        # they need additional time to pair. We need to be patient during this process. */
        self.timerSlac = CONNMGR_TIMER_MAX_20s

    def SdpOk(self):
        self.timerSDP = CONNMGR_TIMER_MAX

    def TcpOk(self):
        self.timerTCP = CONNMGR_TIMER_MAX_10s

    def ApplOk(self, time_in_seconds=10):
        # The application confirmed to have communication. It can decide, based on its state,
        # how long the confirmation shall hold. Default is ten seconds.
        self.timerAppl = time_in_seconds * CONNMGR_CYCLES_PER_SECOND


def testCallbackAddToTrace(s):
    print("callbackAddToTrace: " + s)

def testCallbackShowStatus(s):
    print("callbackShowStatus: " + s)

if __name__ == "__main__":
    print("Testing ConnectionManager...")
    cm = connMgr(testCallbackAddToTrace, testCallbackShowStatus)
    print("connection level " + str(cm.getConnectionLevel()))
    cm.mainfunction()
    print("connection level " + str(cm.getConnectionLevel()))
    cm.SlacOk()
    cm.mainfunction()
    print("connection level " + str(cm.getConnectionLevel()))
    for i in range(1000):
        cm.mainfunction()
    cm.ModemFinderOk(1)
    for i in range(1000):
        cm.mainfunction()
    cm.ModemFinderOk(2)
    for i in range(1000):
        cm.mainfunction()
    cm.SdpOk()
    for i in range(1000):
        cm.mainfunction()
    cm.TcpOk()
    for i in range(1000):
        cm.mainfunction()
    cm.ApplOk()
    for i in range(1000):
        cm.mainfunction()
