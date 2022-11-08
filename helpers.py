

def twoCharHex(b):
    strHex = "%0.2X" % b
    return strHex

def showAsHex(mybytearray, description=""):
    packetlength = len(mybytearray)
    strHex = ""
    for i in range(0, packetlength):
        strHex = strHex + twoCharHex(mybytearray[i]) + " "
    print(description + "(" + str(packetlength) + "bytes) = " + strHex)

def prettyHexMessage(mybytearray, description=""):
    packetlength = len(mybytearray)
    strHex = ""
    for i in range(0, packetlength):
        strHex = strHex + twoCharHex(mybytearray[i]) + " "
    return description + "(" + str(packetlength) + "bytes) = " + strHex

def prettyMac(macByteArray):
    s=""
    for i in range(0, 5):
       s = s + twoCharHex(macByteArray[i]) + ":"
    s = s + twoCharHex(macByteArray[i])
    return s