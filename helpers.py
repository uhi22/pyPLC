

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

def compactHexMessage(mybytearray):
    packetlength = len(mybytearray)
    strHex = ""
    for i in range(0, packetlength):
        strHex = strHex + twoCharHex(mybytearray[i])
    return strHex

def prettyMac(macByteArray):
    s=""
    length = len(macByteArray)
    if (length!=6):
        s="invalid MAC length " + str(length) + "!"
    for i in range(0, length-1):
       s = s + twoCharHex(macByteArray[i]) + ":"
    s = s + twoCharHex(macByteArray[length-1])
    return s
    
def combineValueAndMultiplier(value, mult):
    # input: value and multipliers as strings
    # output: The numerical value x* 10^mult
    x = float(value)
    m = int(mult)
    return x * 10**m

if __name__ == "__main__":
    print("Testing the helpers")
    print(str(combineValueAndMultiplier("123", "0")) + " should be 123")
    print(str(combineValueAndMultiplier("5678", "-1")) + " should be 567.8")
    print(str(combineValueAndMultiplier("-17", "1")) + " should be -170")
    print(str(combineValueAndMultiplier("4", "4")) + " should be 40000")
    
    