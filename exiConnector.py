

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
# Example data:
#   (1) From the Ioniq:
#     In wireshark: Copy as hex stream
#     01fe8001000000228000dbab9371d3234b71d1b981899189d191818991d26b9b3a232b30020000040040
#     remove the 8 bytes V2GTP header
#     8000dbab9371d3234b71d1b981899189d191818991d26b9b3a232b30020000040040
#   (2) From OpenV2G main_example.appHandshake()
#     8000ebab9371d34b9b79d189a98989c1d191d191818981d26b9b3a232b30010000040001b75726e3a64696e3a37303132313a323031323a4d73674465660020000100880
#
#
#
#
#

from helpers import showAsHex, twoCharHex
import subprocess
import sys
import time




if __name__ == "__main__":

    # Example: This is the first message from the EVCC.
    #  Means: It is an supportedAppProtocolReq message. It provides a list of charging protocols supported by the EVCC.
    #
    # 
    exiframe = [
    0x80, 0x00, 0xdb, 0xab, 0x93, 0x71, 0xd3, 0x23, 0x4b, 0x71, 0xd1, 0xb9, 0x81, 0x89,
    0x91, 0x89, 0xd1, 0x91, 0x81, 0x89, 0x91, 0xd2, 0x6b, 0x9b, 0x3a, 0x23, 0x2b, 0x30, 0x02, 0x00,
    0x00, 0x04, 0x00, 0x40 ]

    print("Testing the exiConnector...")
    pathToOpenV2GExe = "..\\OpenV2Gx\\Release\\OpenV2G.exe";
    s = ""
    for i in range(0, len(exiframe)):
        s = s + twoCharHex(exiframe[i])
    print("exi as hex=" + s)
    param1 = "DH" + s # DH for decode handshake
    start_time = time.time()
    for i in range(0, 10):
        result = subprocess.run(
        [pathToOpenV2GExe, param1], capture_output=True, text=True)
        
    print("--- %s seconds ---" % (time.time() - start_time))
    print("stdout:", result.stdout)
    print("stderr:", result.stderr)
    strConverterResult = result.stdout
    if (strConverterResult.find("ProtocolNamespace=urn:din")>0):
        print("Detected DIN")
        
    param1 = "ED1" # ED for encode DIN, session setup response
    result = subprocess.run([pathToOpenV2GExe, param1], capture_output=True, text=True)    
    print("stdout:", result.stdout)
    print("stderr:", result.stderr)
