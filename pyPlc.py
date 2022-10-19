
# This is a simple Tkinter program, running a main loop and reacting on keys
#
# Tested on Windows10 with python 3.9
#
# https://groups.google.com/g/comp.lang.python/c/dldnjWRX3lE/m/cL69gG3fCAAJ

#------------------------------------------------------------
import tkinter as tk
import time
import pyPlcWorker

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
        lblPevMac['text']=s
        s=""
    if (len(s)>0):
        lblStatus['text']=s
    root.update()

root = tk.Tk()
lastKey = ''
display = tk.Label(root, text='No Key', width=30) # A textual element in the graphical user interface
display.pack()
lblHelp = tk.Label(root, text="x=exit, t=testframe")
lblHelp.pack()
lblStatus = tk.Label(root, text="(Status)")
lblStatus.pack()
lblPevMac = tk.Label(root, text="(pev mac)")
lblPevMac.pack()
lblMode = tk.Label(root, text="(mode)")
lblMode.pack()

# Bind the keyboard handler to all relevant elements:
display.bind('<Key>', storekeyname)
root.bind('<Key>', storekeyname)
cbShowStatus("initialized")
root.update()
worker=pyPlcWorker.pyPlcWorker(cbAddToTrace, cbShowStatus)

nMainloops=0
nKeystrokes=0
while lastKey!="x":
    time.sleep(.05) # 'do some calculation'
    nMainloops+=1
    # print(str(nMainloops) + " " + str(nKeystrokes)) # show something in the console window
    root.update()
    worker.mainfunction()
        
#---------------------------------------------------------------
