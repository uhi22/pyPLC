

# EXI is specified in w3.org/TR/exi
# For decoding and encoding, different decoders are availabe:
#  1.  https://github.com/FlUxIuS/V2Gdecoder
#      https://github.com/FlUxIuS/V2Gdecoder/releases
#      Install java from https://www.java.com/de/download/manual.jsp
#
#      C:\>java -version
#      java version "1.8.0_351"
#      Java(TM) SE Runtime Environment (build 1.8.0_351-b10)
#      Java HotSpot(TM) Client VM (build 25.351-b10, mixed mode, sharing)
#      C:\>
#
#      java -jar V2Gdecoder.jar -e -s 8000dbab9371d3234b71d1b981899189d191818991d26b9b3a232b30020000040040
#      ERROR:  'Premature EOS found while reading data.'
#      <?xml version="1.0" encoding="UTF-8"?><ns4:supportedAppProtocolReq xmlns:ns4="urn:iso:15118:2:2010:AppProtocol" 
#      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:ns3="http://www.w3.org/2001/XMLSchema">
#      <AppProtocol>
#      <ProtocolNamespace>urn:din:70121:2012:MsgDef</ProtocolNamespace>
#      <VersionNumberMajor>2</VersionNumberMajor>
#      <VersionNumberMinor>0</VersionNumberMinor>
#      <SchemaID>1</SchemaID>
#      <Priority>1</Priority>
#      </AppProtocol>
#      </ns4:supportedAppProtocolReq>
#
#  2. OpenV2G from https://github.com/Martin-P/OpenV2G
#      Pro: The schema-specific files are already included as generated C-code, this
#         makes it very fast.
#      Contra: Is only a demo, does not provide an interface which could be used for decoding/encoding.
#      Work in progress: Fork in https://github.com/uhi22/OpenV2Gx, to add a command line interface (and maybe a socket interface).
#
#
#
#
#
#
#

from helpers import showAsHex, twoCharHex
import subprocess
import sys
import time
import json
import os

# Example data:
#   (1) From the Ioniq:
#     In wireshark: Copy as hex stream
#     01fe8001000000228000dbab9371d3234b71d1b981899189d191818991d26b9b3a232b30020000040040
#     remove the 8 bytes V2GTP header
#     8000dbab9371d3234b71d1b981899189d191818991d26b9b3a232b30020000040040
exiHexDemoSupportedApplicationProtocolRequestIoniq="8000dbab9371d3234b71d1b981899189d191818991d26b9b3a232b30020000040040"
#    Command line:
#    ./OpenV2G.exe DH8000dbab9371d3234b71d1b981899189d191818991d26b9b3a232b30020000040040

#    (1b) From the tesla. Source https://github.com/SmartEVSE/SmartEVSE-3/issues/25#issuecomment-1606259381)
exiHexDemoSupportedApplicationProtocolRequestTesla="8000DBAB9371D3234B71D1B981899189D191818991D26B9B3A232B30020000040401B75726E3A7465736C613A64696E3A323031383A4D736744656600001C0100080"
# The BMW iX3 handshake request (one schema, schemaID 0, from https://github.com/SmartEVSE/SmartEVSE-3/issues/25#issuecomment-1606271999)
exiHexDemoSupportedApplicationProtocolRequestBMWiX3="8000DBAB9371D3234B71D1B981899189D191818991D26B9B3A232B30020000000040"

#   (2) From OpenV2G main_example.appHandshake()
#   8000ebab9371d34b9b79d189a98989c1d191d191818981d26b9b3a232b30010000040001b75726e3a64696e3a37303132313a323031323a4d73674465660020000100880
exiHexDemoSupportedApplicationProtocolRequest2="8000ebab9371d34b9b79d189a98989c1d191d191818981d26b9b3a232b30010000040001b75726e3a64696e3a37303132313a323031323a4d73674465660020000100880"
#   Command line:
#   ./OpenV2G.exe DH8000ebab9371d34b9b79d189a98989c1d191d191818981d26b9b3a232b30010000040001b75726e3a64696e3a37303132313a323031323a4d73674465660020000100880

#   (3) SupportedApplicationProtocolResponse
#   80400040
#   Command line:
#   ./OpenV2G.exe DH80400040

#   (4) SessionSetupRequest DIN
#   809a0011d00000
#   Command line:
#   ./OpenV2G.exe DD809a0011d00000

#   (5) SessionSetupResponse DIN
# 809a02004080c1014181c211e0000080
#   ./OpenV2G.exe DD809a02004080c1014181c211e0000080

# (6) CableCheckReq
# "result": "809a001010400000"

# (7) PreChargeReq
# "result": "809a001150400000c80006400000"

# 809a0232417b661514a4cb91e0202d0691559529548c0841e0fc1af4507460c0 SessionSetupRes with NewSessionEstablished
# 809a0232417b661514a4cb91e0A02d0691559529548c0841e0fc1af4507460c0 SessionSetupRes with SequenceError
# 809a021a3b7c417774813311a00120024100c4 ServiceDiscoveryRes
# 809a021a3b7c417774813311a0A120024100c4 ServiceDiscoveryRes with SequenceError
# 809a021a3b7c417774813311c000 ServicePaymentSelectionRes
# 809a021a3b7c417774813311c0A0 ServicePaymentSelectionRes with SequenceError
# 809a021a3b7c417774813310c00200 ContractAuthenticationRes
# 809a021a3b7c417774813310c0A200 ContractAuthenticationRes with SequenceError
# 809a0125e6cecc50800001ec00200004051828758405500080000101844138101c2432c04081436c900c0c000041435ecc044606000200 ChargeParameterDiscovery
# 809a0125e6cecd50810001ec00201004051828758405500080000101844138101c2432c04081436c900c0c000041435ecc044606000200 ChargeParameterDiscovery with  ServiceSelectionInvalid
# 809a0125e6cecc5020004080000400  CableCheckRes
# 809a0125e6cecc5020804080000400  CableCheckRes with "FAILED"
# 809a0125e6cecc516000408000008284de880800  PreChargeRes
# 809a0125e6cecc516080408000008284de880800  PreChargeRes with "FAILED"
# 809a0125e6cecc51400420400000  PowerDeliveryRes
# 809a0125e6cecc51408420400000  PowerDeliveryRes with "FAILED"
# 809a0125e6cecc50e0004080000082867dc8081818000000040a1b64802030882702038486580800 CurrentDemandRes
# 809a0125e6cecc50e0804080000082867dc8081818000000040a1b64802030882702038486580800 CurrentDemandRes with "FAILED"

# Further examples are collected in the DemoExiLog.txt.

# Configuration of the exi converter tool
if os.name == "nt":
    # Windows: Path to the EXI decoder/encoder
    pathToOpenV2GExe = "..\\OpenV2Gx\\Release\\OpenV2G.exe"
else:
    # Linux: Path to the EXI decoder/encoder
    pathToOpenV2GExe = "../OpenV2Gx/Release/OpenV2G.exe";


# Functions
def exiprint(s):
    # todo: print to console or log or whatever
    pass

def exiHexToByteArray(hexString):
    # input: a string with the two-byte-hex representation
    # output: a byte array with the same data.
    # If the convertion fails, we return an empty byte array. 
    hexlen=len(hexString)
    if ((hexlen % 2)!=0):
        print("exiHexToByteArray: unplausible length of " + hexString)
        return bytearray(0)
    exiframe = bytearray(int(hexlen/2)) # two characters in the input string are one byte in the exiframe
    for i in range(0, int(hexlen/2)):
        x = hexString[2*i: 2*i+2]        
        #print("valuestring = " + x)
        try:
            v = int(x, 16)
            #print("value " + hex(v))
            exiframe[i] = v
        except:
            print("exiHexToByteArray: unplausible data " + x)
            return bytearray(0)
    return exiframe

def exiByteArrayToHex(b):
    # input: Byte array
    # output: a string with the two-byte-hex representation of the byte array
    s = ""
    for i in range(0, len(b)):
        s = s + twoCharHex(b[i])
    return s

def addV2GTPHeader(exidata):
    #print("type is " + str(type(exidata)))
    if (str(type(exidata)) == "<class 'str'>"):
        #print("changing type to bytearray")
        exidata = exiHexToByteArray(exidata)
    #print("type is " + str(type(exidata)))
    # takes the bytearray with exidata, and adds a header to it, according to the Vehicle-to-Grid-Transport-Protocol
    exiLen = len(exidata)
    header = bytearray(8) # V2GTP header has 8 bytes
                          # 1 byte protocol version
                          # 1 byte protocol version inverted
                          # 2 bytes payload type
                          # 4 byte payload length
    header[0] = 0x01 # version
    header[1] = 0xfe # version inverted
    header[2] = 0x80 # payload type. 0x8001 means "EXI data"
    header[3] = 0x01 # 
    header[4] = (exiLen >> 24) & 0xff # length 4 byte.
    header[5] = (exiLen >> 16) & 0xff
    header[6] = (exiLen >> 8) & 0xff
    header[7] = exiLen & 0xff
    return header + exidata

def removeV2GTPHeader(v2gtpData):
    #removeV2GTPHeader
    return v2gtpData[8:]

def exiDecode(exiHex, prefix="DH"):
    # input: exi data. Either hexstring, or bytearray or bytes
    #        prefix to select the schema
    # if the input is a byte array, we convert it into hex string. If it is already a hex string, we take it as it is.
    #print("type is " + str(type(exiHex)))
    if (str(type(exiHex)) == "<class 'bytearray'>"):
        #print("changing type to hex string")
        exiHex = exiByteArrayToHex(exiHex)
    if (str(type(exiHex)) == "<class 'bytes'>"):
        #print("changing type to hex string")
        exiHex = exiByteArrayToHex(exiHex)
    #print("type is " + str(type(exiHex)))
    param1 = prefix + exiHex # DH for decode handshake
    #print("exiDecode: trying to decode " + exiHex + " with schema " + prefix)
    result = subprocess.run(
        [pathToOpenV2GExe, param1], capture_output=True, text=True)
    #print("stdout:", result.stdout)
    if (len(result.stderr)>0):
        print("exiDecode ERROR. stderr:" + result.stderr)
    strConverterResult = result.stdout
    return strConverterResult
    
def exiEncode(strMessageName):
    # todo: handle the schema, the message name and the parameters
    # param1 = "Eh" # Eh for encode handshake, SupportedApplicationProtocolResponse
    # param1 = "EDa" # EDa for Encode, Din, SessionSetupResponse
    param1 = strMessageName
    exiprint("[EXICONNECTOR] exiEncode " + param1)
    result = subprocess.run([pathToOpenV2GExe, param1], capture_output=True, text=True)    
    if (len(result.stderr)>0):
        strConverterResult = "exiEncode ERROR. stderr:" + result.stderr
        print(strConverterResult)
    else:
        #print("exiEncode stdout:", result.stdout)
        # Now we have an encoder result in json form, something like:
        # {
        # "info": "",
        # "error": "",
        # "result": "8004440400"
        # }
        try:
            jsondict = json.loads(result.stdout)
            strConverterResult = jsondict["result"]
            strConverterError = jsondict["error"]
            if (len(strConverterError)>0):
                print("[EXICONNECTOR] exiEncode error " + strConverterError)
            #print("strConverterResult is " + str(strConverterResult))
        except:
            strConverterResult = "exiEncode failed to convert json to dict."
            print(strConverterResult)
    return strConverterResult    
    

def testByteArrayConversion(s):
    print("Testing conversion of " + s)
    x = exiHexToByteArray(s)
    newHexString = exiByteArrayToHex(x)
    print("exi as hex=" + newHexString)
    exiWithHeader = addV2GTPHeader(x)
    exiWithHeaderString = exiByteArrayToHex(exiWithHeader)
    print("with V2GTP header=" + exiWithHeaderString)


def testDecoder(strHex, pre="DH", comment=""):
    global nFail
    strHex = strHex.replace(" ", "") # remove blanks
    print("Decoder test for " + comment + " with data " + strHex)
    decoded=exiDecode(strHex, pre)
    print(decoded)
    if (len(comment)>0):
        strExpected = comment
        if (decoded.find(strExpected)>0):
            print("---pass---")
        else:
            print("---***!!!FAIL!!!***---")
            nFail+=1

def testReadExiFromSnifferFile():
    file1 = open('results\\tmp.txt', 'r')
    Lines = file1.readlines()
    for myLine in Lines:
        if (myLine[0:9]=="[SNIFFER]"):
            posOfEqualsign = myLine.find("=")
            s = myLine[posOfEqualsign+1:] # The part after the "=" contains the EXI hex data.
            s = s.replace(" ", "") # Remove blanks
            s = s.replace("\n", "") # Remove line feeds
            #print(s)
            testDecoder(s, "DD", "")

def testReadExiFromExiLogFile(strLogFileName):
    print("Trying to read from ExiLogFile " + strLogFileName)
    try:
        file1 = open(strLogFileName, 'r')
        isFileOk = True
    except:
        print("Could not open " + strLogFileName)
        isFileOk = False
        if (strLogFileName == "PevExiLog.txt"):
            print("This is no problem. The PevExiLog.txt will be created when the pyPLC runs in PevMode, and can be decoded afterwards.")
    if (isFileOk):
        fileOut = open(strLogFileName + '.decoded.txt', 'w')
        # example: "ED 809a02004080c1014181c210b8"
        # example with timestamp: "2022-12-20T08:17:15.055755=ED 809a02004080c1014181c21198"
        Lines = file1.readlines()
        for myLine in Lines:
            posOfEqual=myLine.find("=")
            if (posOfEqual>0):
                # we have an equal-sign. Take the string behind it.
                strToDecode=myLine[posOfEqual+1:]
            else:
                # no equal-sign. Take the complete line.
                strToDecode=myLine
            if (myLine[0]=="#"):
                # take-over comment lines into the output
                print(myLine.replace("\n", ""))
                print(myLine.replace("\n", ""), file=fileOut)
            strDecoderSelection = "" # default: unknown line
            if (strToDecode[1:3]=="D "):
                strDecoderSelection = "D" # it is a DIN message
            if (strToDecode[1:3]=="H ") or (strToDecode[1:3]=="h "):
                strDecoderSelection = "H" # it is a ProtocolHandshake message
                
            if (len(strDecoderSelection)>0): # if we have selected a valid decoder
                posOfSpace=2
                s = strToDecode[posOfSpace+1:] # The part after the " " contains the EXI hex data.
                s = s.replace(" ", "") # Remove blanks
                s = s.replace("\n", "") # Remove line feeds
                #print(s)
                decoded=exiDecode(s, "D"+strDecoderSelection)
                print(myLine.replace("\n", "") + " means:")
                print(decoded)
                print(myLine.replace("\n", "") + " means:", file=fileOut)            
                print(decoded, file=fileOut)            
        fileOut.close()

def testTimeConsumption():
    strHex = "809a001150400000c80006400000"
    pre = "DD"
    tStart = time.time()
    nRuns = 100
    for i in range(0, nRuns):
        decoded=exiDecode(strHex, pre)
    tStop = time.time()
    elapsed_time = tStop - tStart
    print("Decoder: Execution time for " + str(nRuns) + " runs:", elapsed_time, "seconds")

    tStart = time.time()
    nRuns = 100
    for i in range(0, nRuns):
        s = exiEncode("EDC_1122334455667788")
    tStop = time.time()
    elapsed_time = tStop - tStart
    print("Encoder: Execution time for " + str(nRuns) + " runs:", elapsed_time, "seconds")
    

if __name__ == "__main__":
    nFail=0
    print("Testing exiConnector...")
    if (False):
        testTimeConsumption()
        exit()
    if (True):        
        testReadExiFromExiLogFile('DemoExiLog.txt')
        testReadExiFromExiLogFile('PevExiLog.txt')
        exit()
    
    if (False):
        testDecoder("8000ebab9371d34b9b79d189a98989c1d191d191818981d26b9b3a232b30010000040001b75726e3a64696e3a37303132313a323031323a4d73674465660020000100880", pre="DH", comment="supportedAppProtocolReq")
        testDecoder("80400040", pre="DH", comment="supportedAppProtocolRes")

        testDecoder("809a0011d00000", pre="DD", comment="SessionSetupReq")
        testDecoder("809a02004080c1014181c211e0000080", pre="DD", comment="SessionSetupRes")
        testDecoder("809a001198", pre="DD", comment="ServiceDiscoveryReq")
        testDecoder("809a0011a0012002412104", pre="DD", comment="ServiceDiscoveryRes")
        testDecoder("809a0011b2001280", pre="DD", comment="ServicePaymentSelectionReq")
        testDecoder("809a0011c000", pre="DD", comment="ServicePaymentSelectionRes")
        testDecoder("809a00107211400dc0c8c82324701900", pre="DD", comment="ChargeParameterDiscoveryReq")    
        testDecoder("809a001080004820400000c99002062050193080c0c802064c8010190140c80a20", pre="DD", comment="ChargeParameterDiscoveryRes")
        testDecoder("809a001010400000", pre="DD", comment="CableCheckReq")
        testDecoder("809a0010200200000000", pre="DD", comment="CableCheckRes")
        testDecoder("809a001150400000c80006400000", pre="DD", comment="PreChargeReq")
        testDecoder("809a00116002000000320000", pre="DD", comment="PreChargeRes")
    
    if (False):
        print("The request from the Ioniq after the EVSE sent ServicePaymentSelectionRes:")
        testDecoder("809A00113020000A00000000", pre="DD", comment="PowerDeliveryReq")
    if (False):
        #print("The session setup request of the Ioniq:")
        #testDecoder("809A02000000000000000011D01811959401930C00", pre="DD", comment="SessionSetupReq")
        print("Ioniq with pyPlc")
        testDecoder("809a02004080c1014181c2107190000005004061a01e04070c84c02050a02000c2438368040309094820105e0a60", pre="DD") # 2022-11-11, 25.315s ChargeParameterDiscoveryReq
#testDecoder("809a02004080c1014181c21080004820400000c99002062050193080c0c802064c8010190140c80a20", pre="DD") # 2022-11-11, 25.408s ChargeParamDisc Res
        
        #testDecoder("809a02004080c1014181c210200200000000", pre="DD") # 2022-11-11, 26.32s CableCheckRes
        #testDecoder("809a02004080c1014181c2116002000000320000", pre="DD") # 2022-11-11, 27.659s PrechargeRes
        #print("A ChargeParameterDiscoveryReq")        
        #testDecoder("809a00107211400dc0c8c82324701900", pre="DD", comment="ChargeParameterDiscoveryReq")
    if (False):
        print("From  https://openinverter.org/forum/viewtopic.php?p=54692#p54692")
        testDecoder("809A0233EBC74AB099A6DC907191400500C8C82324701900", pre="DD") # from https://openinverter.org/forum/viewtopic.php?p=54692#p54692

    if (False):
        testDecoder("80 9A 02 00 40 80 C1 01 41 81 C2 11 E0 00 00 80", pre="DD", comment="SessionSetupRes")
        testDecoder("80 9A 02 00 40 80 C1 01 41 81 C2 11 94 00", pre="DD", comment="ServiceDiscoveryReq")
        testDecoder("80 9A 02 00 40 80 C1 01 41 81 C2 11 A0 01 20 02 41 00 84", pre="DD", comment="ServiceDiscoveryRes")
        testDecoder("80 9A 02 00 40 80 C1 01 41 81 C2 11 B2 00 12 80", pre="DD", comment="ServicePaymentSelectionReq")
        testDecoder("80 9A 02 00 40 80 C1 01 41 81 C2 11 C0 00", pre="DD", comment="ServicePaymentSelectionRes")
        print("The error response of the Ioniq with FAILED_ChargingSystemIncompatibility")
        testDecoder("80 9A 02 00 40 80 C1 01 41 81 C2 11 30 20 00 0A 00 00 00 00", pre="DD", comment="PowerDeliveryReq")
        
        print("The request of the Ioniq after ServicePaymentSelectionResponse")
        testDecoder("80 9A 02 00 40 80 C1 01 41 81 C2 10 B8", pre="DD", comment="ContractAuthenticationReq")
    if (False):        
        print("The response of the Alpi chargeParameterDiscovery")
        testDecoder("80 9A 02 00 00 00 00 03 1F DC 8B D0 80 02 00 00 00 00 00 10 00 2A 80 04 00 00 14 0C 00 40 80 E1 8A 3A 0A 0A 00 A0 60 60 00 08 0A 01 E2 30 30 06 10", pre="DD", comment="ChargeParameterDiscoveryRes")


    if (False):
        testDecoder("809a00113060", pre="DD", comment="PowerDeliveryReq")
        testDecoder("809a0011400420400000", pre="DD", comment="PowerDeliveryRes")
        testDecoder("809a0010d0400000c800410c8000", pre="DD", comment="CurrentDemandReq")
        testDecoder("809a0010e0020000003200019000000600", pre="DD", comment="CurrentDemandRes")
        testDecoder("809a001210400000", pre="DD", comment="WeldingDetectionReq")
        testDecoder("809a00122002000000320000", pre="DD", comment="WeldingDetectionRes")
        testDecoder("809a0011f0", pre="DD", comment="SessionStopReq")
        testDecoder("809a00120000", pre="DD", comment="SessionStopRes")
    
    print("Number of fails: " + str(nFail))
    

        
    #print("Testing exiDecode with exiHexDemoSupportedApplicationProtocolRequestIoniq")
    #print(exiDecode(exiHexDemoSupportedApplicationProtocolRequestIoniq))
    #print("Testing exiDecode with exiHexDemoSupportedApplicationProtocolRequest2")
    #strConverterResult = exiDecode(exiHexDemoSupportedApplicationProtocolRequest2)
    #print(strConverterResult)

    #strConverterResult = exiDecode(exiHexToByteArray(exiHexDemoSupportedApplicationProtocolRequest2))
    #print(strConverterResult)
        
