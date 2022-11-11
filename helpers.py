

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
    length = len(macByteArray)
    if (length!=6):
        s="invalid MAC length " + str(length) + "!"
    for i in range(0, length-1):
       s = s + twoCharHex(macByteArray[i]) + ":"
    s = s + twoCharHex(macByteArray[length-1])
    return s