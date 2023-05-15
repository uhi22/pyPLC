
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


root = Tk()
root.geometry("600x500")
lastKey = ''
lblHelp = Label(root, justify= "left")
lblHelp['text']="press ctrl C to exit"
lblHelp.pack()

canvas_width = 590
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

inputFileName = "local/pcaps_converted/2023-05-12_170340_tcpdump.pcap.values.txt"
fileIn = open(inputFileName, 'r')
Lines = fileIn.readlines()

strCh1Color="#FFFF00" # yellow
strCh2Color="#10FF10" # green
strCh3Color="#4040FF" # blue

strChannelName1=""
strChannelName2=""
strChannelName3=""
ch1values = []
ch2values = []
ch3values = []
count = 0
for line in Lines:
    count += 1
    p1 = line.find("] ")
    p2 = line.find("=")
    if (p1>0) and (p2>p1+3):
        s = line[p1+2:p2]
        if (strChannelName1==""):
            strChannelName1=s
        else:
            if ((strChannelName2=="") and (s!=strChannelName1)):
                strChannelName2=s
            else:
                if ((strChannelName3=="") and (s!=strChannelName1) and (s!=strChannelName2)):
                    strChannelName3=s
        if (s==strChannelName1):
            sVal=line[p2+1:].strip()
            ch1values.append(float(sVal))
        if (s==strChannelName2):
            sVal=line[p2+1:].strip()
            ch2values.append(float(sVal))
        if (s==strChannelName3):
            sVal=line[p2+1:].strip()
            ch3values.append(float(sVal))
    #print("Line{}: {}".format(count, line.strip()))
fileIn.close()

# Hack: look which channel has the most samples.
# Todo: This is not correct, because we have to use the time stamp instead of the sample number.
maxSamples = 1
if maxSamples<len(ch1values):
    maxSamples=len(ch1values)
if maxSamples<len(ch2values):
    maxSamples=len(ch2values)
if maxSamples<len(ch3values):
    maxSamples=len(ch3values)
dxPerSample = xSizeScope / maxSamples

vMin=ch1values[0]
vMax=ch1values[0]
for v in ch1values:
    #print(v)
    if (v<vMin):
        vMin = v
    if (v>vMax):
        vMax = v

print("min=" + str(vMin) + ", max=" + str(vMax))
vDelta = vMax - vMin
perDiv1 = 1
if (vDelta/perDiv1>10):
    perDiv1=2
if (vDelta/perDiv1>10):
    perDiv1=5
if (vDelta/perDiv1>10):
    perDiv1=10
if (vDelta/perDiv1>10):
    perDiv1=20
if (vDelta/perDiv1>10):
    perDiv1=50
if (vDelta/perDiv1>10):
    perDiv1=100
print("Scale: " + str(perDiv1) + "/div")

offs1 = 0
while ((offs1+perDiv1)<vMin):
    offs1+=perDiv1
print("Offset: " + str(offs1))

x =  x0Scope
for v in ch1values:
    yPix =  y0Scope+ySizeScope - (v - offs1)/perDiv1 * ySizeScope / divisionsPerScreen
    x1, y1 = ( x - 1 ), ( yPix - 1 )
    x2, y2 = ( x + 1 ), ( yPix + 1 )
    c.create_line(x1, y1, x2, y2, fill=strCh1Color)
    c.create_line(x1, y2, x2, y1, fill=strCh1Color)
    x+=dxPerSample

vMin=ch2values[0]
vMax=ch2values[0]
for v in ch2values:
    #print(v)
    if (v<vMin):
        vMin = v
    if (v>vMax):
        vMax = v

print("min=" + str(vMin) + ", max=" + str(vMax))
vDelta = vMax - vMin
perDiv2 = 1
if (vDelta/perDiv2>10):
    perDiv2=2
if (vDelta/perDiv2>10):
    perDiv2=5
if (vDelta/perDiv2>10):
    perDiv2=10
if (vDelta/perDiv2>10):
    perDiv2=20
if (vDelta/perDiv2>10):
    perDiv2=50
if (vDelta/perDiv2>10):
    perDiv2=100
print("Scale: " + str(perDiv2) + "/div")

offs2 = 0
while ((offs2+perDiv2)<vMin):
    offs2+=perDiv2
print("Offset: " + str(offs2))

x =  x0Scope
for v in ch2values:
    yPix =  y0Scope+ySizeScope - (v - offs2)/perDiv2 * ySizeScope / divisionsPerScreen
    x1, y1 = ( x - 1 ), ( yPix - 1 )
    x2, y2 = ( x + 1 ), ( yPix + 1 )
    c.create_line(x1, y1, x2, y2, fill=strCh2Color)
    c.create_line(x1, y2, x2, y1, fill=strCh2Color)
    x+=dxPerSample


vMin=ch3values[0]
vMax=ch3values[0]
for v in ch3values:
    print(v)
    if (v<vMin):
        vMin = v
    if (v>vMax):
        vMax = v

print("min=" + str(vMin) + ", max=" + str(vMax))
vDelta = vMax - vMin
perDiv3 = 1
if (vDelta/perDiv3>10):
    perDiv3=2
if (vDelta/perDiv3>10):
    perDiv3=5
if (vDelta/perDiv3>10):
    perDiv3=10
if (vDelta/perDiv3>10):
    perDiv3=20
if (vDelta/perDiv3>10):
    perDiv3=50
if (vDelta/perDiv3>10):
    perDiv3=100
print("Scale: " + str(perDiv3) + "/div")

offs3 = 0
while ((offs3+perDiv3)<vMin):
    offs3+=perDiv3
print("Offset: " + str(offs3))

x =  x0Scope
for v in ch3values:
    yPix =  y0Scope+ySizeScope - (v - offs3)/perDiv3 * ySizeScope / divisionsPerScreen
    x1, y1 = ( x - 3 ), ( yPix - 3 )
    x2, y2 = ( x + 3 ), ( yPix + 3 )
    c.create_line(x1, y1, x2, y2, fill=strCh3Color)
    c.create_line(x1, y2, x2, y1, fill=strCh3Color)
    x+=dxPerSample


    
y0Legend = 0
ySizeLegend = 40
# legend background
c.create_rectangle(x0Scope, y0Legend, x0Scope+xSizeScope,  y0Legend+ySizeLegend, fill="black")

c.create_text(x0Scope,y0Legend+0, text=strChannelName1, anchor="nw", fill=strCh1Color)
c.create_text(x0Scope,y0Legend+10, text=str(perDiv1) + "/div", anchor="nw", fill=strCh1Color)
c.create_text(x0Scope,y0Legend+20, text="Offs " + str(offs1), anchor="nw", fill=strCh1Color)

c.create_text(x0Scope+150,y0Legend+0, text=strChannelName2, anchor="nw", fill=strCh2Color)
c.create_text(x0Scope+150,y0Legend+10, text=str(perDiv2) + "/div", anchor="nw", fill=strCh2Color)
c.create_text(x0Scope+150,y0Legend+20, text="Offs " + str(offs2), anchor="nw", fill=strCh2Color)

c.create_text(x0Scope+300,y0Legend+0, text=strChannelName3, anchor="nw", fill=strCh3Color)
c.create_text(x0Scope+300,y0Legend+10, text=str(perDiv3) + "/div", anchor="nw", fill=strCh3Color)
c.create_text(x0Scope+300,y0Legend+20, text="Offs " + str(offs3), anchor="nw", fill=strCh3Color)

lastKey = ''

root.update()
nMainloops=0
while lastKey!="x":
    time.sleep(.03) # 'do some calculation'
    nMainloops+=1
    # print(str(nMainloops) + " " + str(nKeystrokes)) # show something in the console window
    root.update()
