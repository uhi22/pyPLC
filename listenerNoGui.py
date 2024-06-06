#!/usr/bin/python3
# The non-GUI variant of the listener

# Functionality:
#  - gets the GPS location from a GPS daemon (gpsd on linux)
#  - gets the chargers MAC address from the address manager
#  - sends the location and the chargers MAC to a server via http request

import time
import pyPlcWorker
from pyPlcModes import *
import sys # for argv
from configmodule import getConfigValue, getConfigValueBool
import urllib.request
import gps               # the gpsd interface module

startTime_ms = round(time.time()*1000)
GPSsession = gps.gps(mode=gps.WATCH_ENABLE)
strGpsPos = "no_pos"
strLoggingUrl = getConfigValue("logging_url")

def cbAddToTrace(s):
    currentTime_ms = round(time.time()*1000)
    dT_ms = currentTime_ms - startTime_ms
    print("[" + str(dT_ms) + "ms] " + s)

def cbShowStatus(s, selection=""):
    pass

def trySomeHttp():
    print("***************trying some http********************")
    strChargerMac = "chargerMac=na"
    if (worker.addressManager.isEvseMacNew()):
        strChargerMac = "chargerMac=" + worker.addressManager.getEvseMacAsStringAndClearUpdateFlag().replace(":", "")
    strParams = strChargerMac
    strParams = strParams + "&loops="+str(nMainloops)+"&pos="+strGpsPos
    try:
        contents = urllib.request.urlopen(strLoggingUrl + "?" + strParams).read()
    except Exception as err:
        contents = "(no contents received) " + str(err)
    print(contents)

def GpsMainfunction():
    global strGpsPos
    GPSsession.read()
    if (gps.MODE_SET & GPSsession.valid):
        print('Mode: %s(%d) Time: ' %
              (("Invalid", "NO_FIX", "2D", "3D")[GPSsession.fix.mode],
               GPSsession.fix.mode), end="")
        # print time, if we have it
        if gps.TIME_SET & GPSsession.valid:
            print(GPSsession.fix.time, end="")
        else:
            print('n/a', end="")

        if ((gps.isfinite(GPSsession.fix.latitude) and
             gps.isfinite(GPSsession.fix.longitude))):
            print(" Lat %.6f Lon %.6f" %
                  (GPSsession.fix.latitude, GPSsession.fix.longitude))
            strGpsPos = str(GPSsession.fix.latitude)+"_"+str(GPSsession.fix.longitude)
        else:
            print(" Lat n/a Lon n/a")
            strGpsPos = str(0.0)+"_"+str(0.0)
            print(strGpsPos)
    
myMode = C_LISTEN_MODE


isSimulationMode=0
if (len(sys.argv) > 1):
    if (sys.argv[1] == "S"):
        isSimulationMode=1

print("starting in LISTEN_MODE")
print("press Ctrl-C to exit")

worker=pyPlcWorker.pyPlcWorker(cbAddToTrace, cbShowStatus, myMode, isSimulationMode)

nMainloops=0
httpTime_ms = round(time.time()*1000)
intervalForHttpLogging_ms = 15000 # each 15s send the logging data to the server

while (1):
    time.sleep(.03) # 'do some calculation'
    nMainloops+=1
    currentTime_ms = round(time.time()*1000)
    if ((currentTime_ms-httpTime_ms)>intervalForHttpLogging_ms) or (worker.addressManager.isEvseMacNew()):
        trySomeHttp()
        httpTime_ms = currentTime_ms
    worker.mainfunction()
    GpsMainfunction()
        
#---------------------------------------------------------------
