
# The non-GUI variant of the EVSE side

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
soc_fallback_energy_capacity = getConfigValue("soc_fallback_energy_capacity")

def socStatusCallback(current_soc: int, full_soc: int = -1, energy_capacity: int = -1, energy_request: int = -1, evccid: str = "", origin: str = ""):
    # Do some basic value checks and conversions
    # Some cars do not support certain values and return 0, make sure we actually send -1

    if (energy_capacity > 0):
       # We need Wh, not something in between kWh and Wh
       energy_capacity = energy_capacity * 10
    else:
       # Some cars do not supply energy capacity of their battery
       # Support some kind of fallback value which would work for installations where typically one car charges
       if (int(soc_fallback_energy_capacity) > 0):
          energy_capacity = int(soc_fallback_energy_capacity) * 10
       else:
          energy_capacity = -1

    if (energy_request > 0):
       # We need Wh, not something in between kWh and Wh
       energy_request = energy_request * 10
    else:
       energy_request = -1

    print(f"Received SoC status from {origin}.\n"
          f"    Current SoC {current_soc}% \n"
          f"    Full SoC {full_soc}%\n"
          f"    Energy capacity {energy_capacity} Wh \n"
          f"    Energy request {energy_request} Wh \n"
          f"    EVCCID {evccid} \n")

    if soc_callback_enabled:
        requests.post(f"{soc_callback_url}?current_soc={current_soc}&full_soc={full_soc}&energy_capacity={energy_capacity}&energy_request={energy_request}&evccid={evccid}")

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
