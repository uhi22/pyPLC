
# The non-GUI variant of the PEV side

import time
import pyPlcWorker
from configmodule import getConfigValue, getConfigValueBool
from pyPlcModes import *
import sys # for argv
import requests

startTime_ms = round(time.time()*1000)

def cbAddToTrace(s):
    currentTime_ms = round(time.time()*1000)
    dT_ms = currentTime_ms - startTime_ms
    print("[" + str(dT_ms) + "ms] " + s)

def cbShowStatus(s, selection=""):
    pass


soc_callback_enabled = getConfigValueBool("soc_callback_enabled")
soc_callback_url = getConfigValue("soc_callback_endpoint") if soc_callback_enabled else ""

def socStatusCallback(remaining_soc: int, full_soc: int = -1, bulk_soc: int = -1, origin: str = ""):
    print(f"Received SoC status from {origin}.\n"
          f"    Remaining {remaining_soc}% \n"
          f"    Full at {full_soc}%\n"
          f"    Bulk at {bulk_soc}%")
    if soc_callback_enabled:
        requests.post(f"{soc_callback_url}/modem?remaining_soc={remaining_soc}&full_soc={full_soc}&bulk_soc={bulk_soc}")

myMode = C_EVSE_MODE

print("starting in EVSE_MODE")
print("press Ctrl-C to exit")

worker=pyPlcWorker.pyPlcWorker(cbAddToTrace, cbShowStatus, myMode, 0, socStatusCallback)

nMainloops=0
while (1):
    time.sleep(.03) # 'do some calculation'
    nMainloops+=1
    worker.mainfunction()
        
#---------------------------------------------------------------
