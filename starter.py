
# https://noisefloor-net.blogspot.com/2015/10/systemd-timer-unter-raspbian.html
# In  /etc/systemd/system we need to create 2 files:
#  pevStarter.service
#  pevStarter.timer
# cd /etc/systemd/system
# sudo nano pevStarter.service
#  ... add content...
# sudo nano pevStarter.timer
#  ... add content ...
# Make executable:
# sudo chmod +x pevStarter.*
# start and enable the unit:
# sudo systemctl start pevStarter.timer
# sudo systemctl enable pevStarter.timer

# https://gist.github.com/emxsys/a507f3cad928e66f6410e7ac28e2990f

# View log:
#  journalctl --unit=pevStarter

# sudo systemctl status pevStarter

import subprocess
import datetime
from time import sleep


def writeStartLog():
    file_object = open('/home/pi/myprogs/pyPlc/starterlog.txt', 'a')
    now = datetime.datetime.now()
    s = str(now)
    file_object.write("starter was started at " + s + "\n") 
    file_object.close()

def checking():
    file_object = open('/home/pi/myprogs/pyPlc/starterlog.txt', 'a')
    #file_object.write('hello\n')
    now = datetime.datetime.now()
    s = str(now)
    file_object.write("It is " + s + "\n") 

    command = "ps"
    param1 = "axj"
    result = subprocess.run(
            [command, param1], capture_output=True, text=True)

    if (len(result.stderr)>0):
        strOut = "Error:" + result.stderr + "\n"
    else:
        strOut = result.stdout

    blRunning=False
    lines = strOut.split("\n")
    for line in lines:
        if (line.find("pevNoGui.py")>0):
            blRunning = True

    if (blRunning):
        file_object.write("its running\n")
    else:
        file_object.write("its NOT running. Trying to start...\n")
        #processvar = subprocess.Popen(["python", "/home/pi/myprogs/pyPlc/pevNoGui.py"])
        result = subprocess.run(["python", "/home/pi/myprogs/pyPlc/pevNoGui.py"])
        if (len(result.stderr)>0):
            strOut = "Error:" + result.stderr + "\n"
        else:
            strOut = ""
        strOut = "done\n"
        file_object.write(strOut)
        
    file_object.close()


try:
    writeStartLog()
    while True:
        #print("Hello World")
        checking()
        sleep(10)
except KeyboardInterrupt as e:
    print("Stopping...")
    