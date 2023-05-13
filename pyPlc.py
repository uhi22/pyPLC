
# This is a simple Tkinter program, running a main loop and reacting on keys
#
# Tested on Windows10 with python 3.9
#
# https://groups.google.com/g/comp.lang.python/c/dldnjWRX3lE/m/cL69gG3fCAAJ

#------------------------------------------------------------
import tkinter as tk
import time
import pyPlcWorker
from pyPlcModes import *
import sys # for argv
from configmodule import getConfigValue, getConfigValueBool
from mytestsuite import * 

startTime_ms = round(time.time()*1000)

def storekeyname(event):
    global nKeystrokes
    global lastKey
    nKeystrokes+=1
    lastKey = event.keysym
    worker.handleUserAction(lastKey)
    return 'break' # swallow the event

def inkey():
    global lastKey
    return lastKey
    lastKey = ''

def cbAddToTrace(s):
    currentTime_ms = round(time.time()*1000)
    dT_ms = currentTime_ms - startTime_ms
    print("[" + str(dT_ms) + "ms] " + s)

def cbShowStatus(s, selection=""):
    #print(s)
    if (selection == "mode"):
        lblMode['text']=s
        s=""
    if (selection == "pevmac"):
        lblPevMac['text']="PEV MAC " + s
        s=""
    if (selection == "uInlet"):
        lblUInlet['text']= "UInlet " + s + "V"
        s=""
    if (selection == "EVSEPresentVoltage"):
        lblEVSEPresentVoltage['text']= "EVSEPresentVoltage " + s + "V"
        s=""
    if (selection == "pevState"):
        lblState['text']= s
        s=""
    if (selection == "evseState"):
        lblState['text']= s
        s=""
    if (selection == "soc"):
        lblSoc['text']= "SOC " + s + "%"
        s=""
    if (len(s)>0):
        lblStatus['text']=s
    root.update()

myMode = C_LISTEN_MODE
if (getConfigValue("mode")=="PevMode"):
    myMode = C_PEV_MODE
if (getConfigValue("mode")=="EvseMode"):
    myMode = C_EVSE_MODE
# The command line arguments overwrite the config file setting for PevMode/EvseMode.
if (len(sys.argv) > 1):
    if (sys.argv[1] == "P"):
        myMode = C_PEV_MODE
    else:
        if (sys.argv[1] == "E"):
            myMode = C_EVSE_MODE

# The simulation mode can be set by command line in addition in both, PevMode and EvseMode.
isSimulationMode=0
if (len(sys.argv) > 2):
    if (sys.argv[2] == "S"):
        isSimulationMode=1

if (myMode == C_LISTEN_MODE):
    print("starting in LISTEN_MODE")
if (myMode == C_PEV_MODE):
    if (isSimulationMode!=0):
        print("starting in PevMode, simulated environment")
    else:
        print("starting in PevMode")
if (myMode == C_EVSE_MODE):
    if (isSimulationMode!=0):
        print("starting in EvseMode, simulated environment")
    else:
        print("starting in EvseMode")
 
root = tk.Tk()
root.geometry("400x350")
lastKey = ''
lblHelp = tk.Label(root, justify= "left")
lblHelp['text']="x=exit \nS=GET_SW \nP=PEV mode \nE=EVSE mode \nL=Listen mode \ns=SET_KEY \nG=GET_KEY (try twice) \nt=SET_KEY modified \n space=stop charging"
lblHelp.pack()
lblStatus = tk.Label(root, text="(Status)")
lblStatus.pack()
lblPevMac = tk.Label(root, text="(pev mac)")
lblPevMac.pack()
lblState = tk.Label(root, text="(state)")
lblState.config(font=('Helvetica bold', 20))
lblState.pack()
lblSoc = tk.Label(root, text="(soc)")
lblSoc.pack()
lblUInlet = tk.Label(root, text="(U Inlet)")
lblUInlet.config(font=('Helvetica bold', 26))
lblUInlet.pack()
lblEVSEPresentVoltage = tk.Label(root, text="(EVSEPresentVoltage)")
lblEVSEPresentVoltage.config(font=('Helvetica bold', 16))
lblEVSEPresentVoltage.pack()

if (myMode == C_EVSE_MODE):
    lblTestcase = tk.Label(root, text="(test case)")
    lblTestcase.pack()

lblMode = tk.Label(root, text="(mode)")
lblMode.pack()

if (myMode != C_PEV_MODE):
    lblUInlet['text']= ""

nKeystrokes=0
# Bind the keyboard handler to all relevant elements:
root.bind('<Key>', storekeyname)
cbShowStatus("initialized")
root.update()
worker=pyPlcWorker.pyPlcWorker(cbAddToTrace, cbShowStatus, myMode, isSimulationMode)

nMainloops=0
while lastKey!="x":
    time.sleep(.03) # 'do some calculation'
    nMainloops+=1
    # print(str(nMainloops) + " " + str(nKeystrokes)) # show something in the console window
    root.update()
    worker.mainfunction()
    if (myMode == C_EVSE_MODE):
        lblTestcase['text']= "Testcase " + str(testsuite_getTcNumber())

del(worker)
        
#---------------------------------------------------------------
