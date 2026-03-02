
class cableChecker():
    def __init__(self, powersupplyinterface):
        self.psu = powersupplyinterface
        self.cableCheckTimer = 0
        self.isFinished = False
        self.cableCheckMaxTime = 50 # 100 is ~ 10s
        self.cableCheckTargetVoltage = 300
        self.cableCheckError = 0

    def triggerCableCheck(self):
        if (self.cableCheckTimer==0):
            self.cableCheckTimer=1
            
    def isCableCheckFinished(self):
        return self.isFinished

    def isCableCheckOk(self):
        if (self.cableCheckError == 0):
            return True
        else:
            return False

    def runCheckStep1(self):
        print("cableChecker runCheckStep1")
        # select weak supply
        self.psu.selectDriverForCableCheck()
        # turn-on the HV
        self.psu.setVoltage(self.cableCheckTargetVoltage)
        print("cable check applies " + str(self.cableCheckTargetVoltage) + " V")
        
    def evaluateResultAndCleanUp(self):
        print("cableChecker evaluating results and cleaning up")
        # read cable voltage
        u = self.psu.readPhysicalVoltage()
        print("measured voltage: " + str(u))
        # decide whether good or bad
        if (u<self.cableCheckTargetVoltage-30):
            self.cableCheckError = 1
            print("cable check error: voltage too low")
        if (u>self.cableCheckTargetVoltage+30):
            self.cableCheckError = 2
            print("cable check error: voltage too high")
        # turn voltage off
        self.psu.setVoltage(0)
        self.isFinished = True
        
    def resetCableCheck(self):
        self.cableCheckTimer = 0
        self.isFinished = False
        self.cableCheckError = 0
        
    def mainfunction(self):
        if (self.cableCheckTimer==1):
            # CableCheck just started
            self.runCheckStep1()
        if (self.cableCheckTimer==self.cableCheckMaxTime-1):
            # CableCheck nearly finished
            self.evaluateResultAndCleanUp()
        if (self.cableCheckTimer>0) and (self.cableCheckTimer<=self.cableCheckMaxTime):
            # count the cableCheckTimer, if it is not halted and not expired
            self.cableCheckTimer+=1

        