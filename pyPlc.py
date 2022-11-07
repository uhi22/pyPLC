
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
    print(s)

def cbShowStatus(s, selection=""):
    #print(s)
    if (selection == "mode"):
        lblMode['text']=s
        s=""
    if (selection == "pevmac"):
        lblPevMac['text']="PEV MAC " + s
        s=""
    if (len(s)>0):
        lblStatus['text']=s
    root.update()

myMode = C_LISTEN_MODE
if (len(sys.argv) > 1):
    if (sys.argv[1] == "P"):
        myMode = C_PEV_MODE
    else:
        if (sys.argv[1] == "E"):
            myMode = C_EVSE_MODE

if (myMode == C_LISTEN_MODE):
    print("starting in LISTEN_MODE")
if (myMode == C_PEV_MODE):
    print("starting in PEV_MODE")
if (myMode == C_EVSE_MODE):
    print("starting in EVSE_MODE")
 
root = tk.Tk()
lastKey = ''
lblHelp = tk.Label(root, justify= "left")
lblHelp['text']="x=exit \nS=GET_SW \nP=PEV mode \nE=EVSE mode \nL=Listen mode \ns=SET_KEY \nG=GET_KEY (try twice) \nt=SET_KEY modified"
lblHelp.pack()
lblStatus = tk.Label(root, text="(Status)")
lblStatus.pack()
lblPevMac = tk.Label(root, text="(pev mac)")
lblPevMac.pack()
lblMode = tk.Label(root, text="(mode)")
lblMode.pack()

# Bind the keyboard handler to all relevant elements:
root.bind('<Key>', storekeyname)
cbShowStatus("initialized")
root.update()
worker=pyPlcWorker.pyPlcWorker(cbAddToTrace, cbShowStatus, myMode)

nMainloops=0
nKeystrokes=0
while lastKey!="x":
    time.sleep(.05) # 'do some calculation'
    nMainloops+=1
    # print(str(nMainloops) + " " + str(nKeystrokes)) # show something in the console window
    root.update()
    worker.mainfunction()
        
#---------------------------------------------------------------
