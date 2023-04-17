
# pcap Converter
#
# This little helper tool read a network trace (e.g. recorded with wireshark) and
# interprets the content of the EXI.V2GTP.TCP.IPv6 data.
#
# Preconditions:
# 1. You have a capture file with contains V2G traffic (pcap or pcapng file).
# 2. You installed the python library pyshark, according to https://github.com/KimiNewt/pyshark/
#    pip install pyshark
# 3. You cloned and compiled the OpenV2Gx EXI decoder from https://github.com/uhi22/OpenV2Gx 

import pyshark
import exiConnector
import os


def convertPcapToTxt(inputFileName):
    cap = pyshark.FileCapture(inputFileName, display_filter="ipv6")
    fileOut = open(inputFileName + '.decoded.txt', 'w')
    #print(cap)
    #print(cap[0])
    #print(cap[1])
    #print(dir(cap[1]))
    #print(cap[1].sniff_time) # readable time
    #print(cap[1].sniff_timestamp) # epoch time
    numberOfPackets=0
    for packet in cap:
        numberOfPackets+=1
        #print(packet)
        if 'TCP' in packet:
            #print(packet.tcp.field_names)
            if ('payload' in packet.tcp.field_names):
                tcppayload = packet.tcp.payload # this gives a string of hex values, separated by ":", e.g. "01:fe:80:01"
                s = tcppayload.replace(":", "") # remove colons
                if (s[0:8]=="01fe8001"):
                    # it is a V2GTP header with EXI content
                    strExi = s[16:] # remove V2GTP header (8 bytes, means 16 hex characters)
                    sHeader = "Packet #" + str(numberOfPackets) + " [" + str(packet.sniff_time) + "] " + strExi + " means:"
                    pre = "DD" # decode DIN
                    decoded=exiConnector.exiDecode(strExi, pre)
                    print(sHeader)
                    print(decoded)
                    print(sHeader, file=fileOut)
                    print(decoded, file=fileOut)
    fileOut.close()

# assign directory
directory = '../temp'

# iterate over files in
# that directory
for filename in os.listdir(directory):
    f = os.path.join(directory, filename)
    # checking if it is a file
    if os.path.isfile(f):
        print(f)
        if (f[-5:]==".pcap") or (f[-7:]==".pcapng"):
            strFileNameWithPath = f
            print("Will decode " + strFileNameWithPath)
            convertPcapToTxt(strFileNameWithPath)
