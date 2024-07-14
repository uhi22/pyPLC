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
import RPi.GPIO as GPIO # for controlling hardware pins of the raspberry

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

def testBlockingBeep(patternselection):
    if (patternselection==1):
        # The "MAC Found" beep
        p.ChangeDutyCycle(10)
        p.ChangeFrequency(1100)
        time.sleep(0.3)
        p.ChangeFrequency(1300)
        time.sleep(0.3)
        p.ChangeFrequency(1500)
        time.sleep(0.3)
        p.ChangeDutyCycle(0)
    if (patternselection==2):
        # The short "ok" beep
        p.ChangeDutyCycle(10)
        p.ChangeFrequency(1600)
        time.sleep(0.07)
        p.ChangeDutyCycle(0)
    if (patternselection==3):
        # The "no GPS position" beep
        print("no pos beep 4")
        p.ChangeDutyCycle(10)
        p.ChangeFrequency(1700)
        time.sleep(0.04)
        p.ChangeDutyCycle(0)
        time.sleep(0.04)
        p.ChangeDutyCycle(10)
        p.ChangeFrequency(1700)
        time.sleep(0.04)
        p.ChangeDutyCycle(0)
        time.sleep(0.04)
        p.ChangeDutyCycle(10)
        p.ChangeFrequency(1700)
        time.sleep(0.04)
        p.ChangeDutyCycle(0)
        time.sleep(0.04)
        p.ChangeDutyCycle(10)
        p.ChangeFrequency(1700)
        time.sleep(0.04)
        p.ChangeDutyCycle(0)

def trySomeHttp():
    print("***************trying some http********************")
    strChargerMac = "chargerMac=na"
    if (worker.addressManager.isEvseMacNew()):
        testBlockingBeep(1)
        strChargerMac = "chargerMac=" + worker.addressManager.getEvseMacAsStringAndClearUpdateFlag().replace(":", "")
    strParams = strChargerMac
    strParams = strParams + "&loops="+str(nMainloops)+"&pos="+strGpsPos
    print(strParams)
    try:
        contents = urllib.request.urlopen(strLoggingUrl + "?" + strParams).read()
        print(len(strGpsPos))
        if (len(strGpsPos)>7):
            print("Valid GPS coordinates, and http logging worked")
            testBlockingBeep(2)
        else:
            print("http was ok, but no GPS position")
            testBlockingBeep(3)
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
    


    
    

def mytestfunction():
    global soundstate
    #testBlockingBeep(2)
    #if (soundstate==0):
    #    p.ChangeDutyCycle(10)
    #    p.ChangeFrequency(1000)
    #if (soundstate==1):
    #    p.ChangeDutyCycle(10)
    #    p.ChangeFrequency(1200)
    #if (soundstate==2):
    #    p.ChangeDutyCycle(0)
    #soundstate+=1
    #if (soundstate>=3):
    #    soundstate=0
    

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
testTime_ms = httpTime_ms
#intervalForHttpLogging_ms = 120*1000 # each 2 minutes send the logging data to the server
intervalForHttpLogging_ms = 30*1000 # each half minute send the logging data to the server

soundstate = 0
GPIO.setmode(GPIO.BCM)
GPIO.setup(23, GPIO.OUT)
p=GPIO.PWM(23, 500) # 500 Hz
p.start(0)
p.ChangeDutyCycle(50)
time.sleep(0.1)
p.ChangeDutyCycle(0)
time.sleep(0.1)
p.ChangeDutyCycle(50)
time.sleep(0.1)
p.ChangeDutyCycle(0)


while (1):
    time.sleep(.03) # 'do some calculation'
    nMainloops+=1
    currentTime_ms = round(time.time()*1000)
    if ((currentTime_ms-httpTime_ms)>intervalForHttpLogging_ms) or (worker.addressManager.isEvseMacNew()):
        trySomeHttp()
        httpTime_ms = currentTime_ms
    if ((currentTime_ms-testTime_ms)>2000):
        mytestfunction()
        testTime_ms = currentTime_ms
    worker.mainfunction()
    GpsMainfunction()
        
#---------------------------------------------------------------
