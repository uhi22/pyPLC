
# Scope
# Shows data in the style of an oscilloscope.

#
# Todos:
#  - use correct time axis
#  - allow the user to change the scaling
#  - use functions intead of copy&paste code
#  - support more channels
#  - (and more)
#

from tkinter import *
import time
import sys # for argv


def addChannelNameToChannel(s):
    global channelNames
    blAlreadyPresent=0
    for i in range(len(channelNames)):
        if (channelNames[i]==s):
            blAlreadyPresent=1
    if (blAlreadyPresent==1):
        #print("The name " + s + " is already present in the channel names. Nothing to do.")
        return
    # The new name is not known yet. Search an empty channel and store it there.
    for i in range(len(channelNames)):
        if (channelNames[i]==""):
            channelNames[i]=s
            print("Stored " + s + " as channel name for channel " + str(i))
            return
    # if we come here, there was no free channel, and we discard the new name.
    print("Discarding name " + s)


def addChannelData(name, time, value):
    # adds a data point to the channel with the given name
    global channelNames
    global channelData
    for i in range(len(channelNames)):
        if (channelNames[i]==name):
            channelData[i].append([time, float(value)])
            return


root = Tk()
root.geometry("750x500")
lastKey = ''
lblHelp = Label(root, justify= "left")
lblHelp['text']="press ctrl C to exit"
lblHelp.pack()

canvas_width = 750
canvas_height = 400
divisionsPerScreen = 10

c = Canvas(root, 
           width=canvas_width,
           height=canvas_height)
c.pack()

x0Scope = 10
y0Scope = 45
xSizeScope = canvas_width-30
ySizeScope = canvas_height-50
# osci background
c.create_rectangle(x0Scope, y0Scope, x0Scope+xSizeScope,  y0Scope+ySizeScope, fill="black")
# osci divisions
for i in range(1, divisionsPerScreen):
    dx= i*xSizeScope/divisionsPerScreen
    c.create_line(x0Scope+dx, y0Scope, x0Scope+dx, y0Scope+ySizeScope, fill="#404040")
    dy= i*ySizeScope/divisionsPerScreen
    c.create_line(x0Scope, y0Scope+dy, x0Scope+xSizeScope, y0Scope+dy, fill="#404040")
# osci outer border
c.create_line(x0Scope, y0Scope, x0Scope+xSizeScope, y0Scope, fill="#FFFFFF")
c.create_line(x0Scope, y0Scope, x0Scope, y0Scope+ySizeScope, fill="#FFFFFF")
c.create_line(x0Scope+xSizeScope, y0Scope+ySizeScope, x0Scope+xSizeScope, y0Scope, fill="#FFFFFF")
c.create_line(x0Scope+xSizeScope, y0Scope+ySizeScope, x0Scope, y0Scope+ySizeScope, fill="#FFFFFF")

inputFileName = "local/pcaps_to_convert/ccm_spi_ioniq_compleo_full_charge_sequence_ended_on_charger.txt.pcap.values.txt"
fileIn = open(inputFileName, 'r')
Lines = fileIn.readlines()

#                  yellow     green       blue      red         orange
channelColors = ["#FFFF00", "#10FF10", "#4040FF",  "#FF4040", "#FFC000" ]
numberOfChannels = len(channelColors)
print(str(numberOfChannels) + " channels")

channelNames = []
channelData = []

for i in range(numberOfChannels):
    channelNames.append("") # empty string for each channel
    channelData.append([]) # empty list for each channel
channelOffsets = [] # will be appended dynamically below
channelPerDivs = [] # will be appended dynamically below

count = 0
for line in Lines:
    count += 1
    p1 = line.find("[")
    p2 = line.find("] ")
    p3 = line.find("=")
    if (p1>=0) and (p2>p1) and (p3>p2+3):
        strName = line[p2+2:p3]
        addChannelNameToChannel(strName) # assign the found variable name to a channel, if not yet assigned
        strVal=line[p3+1:].strip()
        strTime=line[p1+1:p2].strip()
        #print("Time >"+strTime+"<")
        addChannelData(strName, strTime, strVal)
    #print("Line{}: {}".format(count, line.strip()))
fileIn.close()

print("The channel names")
for i in range(numberOfChannels):
    print(str(i) + " " + channelNames[i])

#print("The channel data")
#for i in range(numberOfChannels):
#    print(str(i) + " " + channelNames[i])    
#    for k in range(len(channelData[i])):
#        t = channelData[i][k][0]
#        y = channelData[i][k][1]
#        print("t= " + t + " y= " + str(y) )

# Hack: look which channel has the most samples.
# Todo: This is not correct, because we have to use the time stamp instead of the sample number.
maxSamples = 1
for i in range(numberOfChannels):
    if maxSamples<len(channelData[i]):
        maxSamples=len(channelData[i])
print("maxSamples " + str(maxSamples))

dxPerSample = xSizeScope / maxSamples

# Auto-scaling of the y axis
for i in range(numberOfChannels):
    vMin=channelData[i][0][1]
    vMax=vMin
    for v in channelData[i]:
        #print(v)
        if (v[1]<vMin):
            vMin = v[1]
        if (v[1]>vMax):
            vMax = v[1]
    print("For channel " + str(i) + " we have min " + str(vMin) + " and max " + str(vMax))
    vDelta = vMax - vMin
    perDiv = 1
    if (vDelta/perDiv>10):
        perDiv=2
    if (vDelta/perDiv>10):
        perDiv=5
    if (vDelta/perDiv>10):
        perDiv=10
    if (vDelta/perDiv>10):
        perDiv=20
    if (vDelta/perDiv>10):
        perDiv=50
    if (vDelta/perDiv>10):
        perDiv=100
    print("Scale: " + str(perDiv) + "/div")

    offs = 0
    while ((offs+perDiv)<vMin):
        offs+=perDiv
    print("Offset: " + str(offs))
    channelOffsets.append(offs)
    channelPerDivs.append(perDiv)


for i in range(numberOfChannels):
    x =  x0Scope
    for v in channelData[i]:
        yPix =  y0Scope+ySizeScope - (v[1] - channelOffsets[i])/channelPerDivs[i] * ySizeScope / divisionsPerScreen
        x1, y1 = ( x - 1 ), ( yPix - 1 )
        x2, y2 = ( x + 1 ), ( yPix + 1 )
        c.create_line(x1, y1, x2, y2, fill=channelColors[i])
        c.create_line(x1, y2, x2, y1, fill=channelColors[i])
        x+=dxPerSample



y0Legend = 0
ySizeLegend = 40
# legend background
c.create_rectangle(x0Scope, y0Legend, x0Scope+xSizeScope,  y0Legend+ySizeLegend, fill="black")

for i in range(numberOfChannels):
    c.create_text(x0Scope+150*i,y0Legend+0, text=channelNames[i], anchor="nw", fill=channelColors[i])
    c.create_text(x0Scope+150*i,y0Legend+10, text=str(channelPerDivs[i]) + "/div", anchor="nw", fill=channelColors[i])
    c.create_text(x0Scope+150*i,y0Legend+20, text="Offs " + str(channelOffsets[i]), anchor="nw", fill=channelColors[i])


lastKey = ''

root.update()
nMainloops=0
while lastKey!="x":
    time.sleep(.03) # 'do some calculation'
    nMainloops+=1
    # print(str(nMainloops) + " " + str(nKeystrokes)) # show something in the console window
    root.update()
