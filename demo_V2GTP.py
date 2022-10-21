

# EXI is specified in w3.org/TR/exi
# To decode and encode, we can use this Decoder/Encoder: https://github.com/FlUxIuS/V2Gdecoder
#
# https://github.com/FlUxIuS/V2Gdecoder/releases
# Install java from https://www.java.com/de/download/manual.jsp
#
# C:\>java -version
# java version "1.8.0_351"
# Java(TM) SE Runtime Environment (build 1.8.0_351-b10)
# Java HotSpot(TM) Client VM (build 25.351-b10, mixed mode, sharing)
# C:\>
#
# In wireshark: Copy as hex stream
# 01fe8001000000228000dbab9371d3234b71d1b981899189d191818991d26b9b3a232b30020000040040
# remove the 8 bytes V2GTP header
# 8000dbab9371d3234b71d1b981899189d191818991d26b9b3a232b30020000040040
#
# java -jar V2Gdecoder.jar -e -s 8000dbab9371d3234b71d1b981899189d191818991d26b9b3a232b30020000040040
# ERROR:  'Premature EOS found while reading data.'
# <?xml version="1.0" encoding="UTF-8"?><ns4:supportedAppProtocolReq xmlns:ns4="urn:iso:15118:2:2010:AppProtocol" 
# xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:ns3="http://www.w3.org/2001/XMLSchema">
# <AppProtocol>
#  <ProtocolNamespace>urn:din:70121:2012:MsgDef</ProtocolNamespace>
#  <VersionNumberMajor>2</VersionNumberMajor>
#  <VersionNumberMinor>0</VersionNumberMinor>
#  <SchemaID>1</SchemaID>
#  <Priority>1</Priority>
# </AppProtocol>
# </ns4:supportedAppProtocolReq>
#
#
#
#

from helpers import showAsHex

# Example: This is the first message from the EVCC.
#  Means: It is an supportedAppProtocolReq message. It provides a list of charging protocols supported by the EVCC.
#
# 
v2gframe = [
0x01, 0xfe,
0x80, 0x01,
0x00, 0x00, 0x00, 0x22,
0x80, 0x00, 0xdb, 0xab, 0x93, 0x71, 0xd3, 0x23, 0x4b, 0x71, 0xd1, 0xb9, 0x81, 0x89,
0x91, 0x89, 0xd1, 0x91, 0x81, 0x89, 0x91, 0xd2, 0x6b, 0x9b, 0x3a, 0x23, 0x2b, 0x30, 0x02, 0x00,
0x00, 0x04, 0x00, 0x40 ]


if (len(v2gframe)<9):
    print("size too small")
else:
    if ((v2gframe[0]!=0x01) or (v2gframe[1]!=0xFE)):
        print("wrong V2GTP version")
    else:
        if ((v2gframe[2]!=0x80) or (v2gframe[3]!=0x01)):
            print("wrong payload type, expecting 0x8001 EXI")
        else:
            exiLen = (v2gframe[4]<<24) + (v2gframe[5]<<16) + (v2gframe[6]<<8) + v2gframe[7]
            print("exiLen=" + str(exiLen))
            if (exiLen+8 != len(v2gframe)):
                print("exiLen does not match actual frame size")
            else:
                print("header ok")
                exiframe = bytearray(exiLen)
                exiframe = v2gframe[8:]
                showAsHex(exiframe, "exiframe ")
                # Header:
                # 80 upper two bits: distinguishing bits 1 0
                #    presenceBitForExiOptions  0 means "no options"
                #    five bits version information: 0 0 0 0 0 means "final version 1"
                #
                # 00 DB AB 93 71 D3 23 4B
