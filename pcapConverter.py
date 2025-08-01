
# pcap Converter
#
# This little helper tool reads a network trace (e.g. recorded with wireshark) and
# interprets the content of the EXI.V2GTP.TCP.IPv6 data.
#
# Preconditions:
# 1. You have a capture file with contains V2G traffic (pcap or pcapng file).
# 2. You installed the python library pyshark, according to https://github.com/KimiNewt/pyshark/
#    pip install pyshark
# 3. You cloned and compiled the OpenV2Gx EXI decoder from https://github.com/uhi22/OpenV2Gx
#
# Limitations:
# - Only DIN is supported at the moment.
# - The script treats all V2G EXI messages as DIN messages. This means, the ApplHandshake messages at
#   the begin of the charging session will lead to wrong or not decoded data.
# - The path where the script look for pcap files needs to be configured in the code.
#
# Possible improvements / Todos:
# - Show also the SLAC, NeigborDiscovery and SDP.
# - Add flexibility to also decode the ApplHandshake messages.
# - Add ISO support.
# - Configure the path where to look for pcap files via command line
#

import pyshark
import exiConnector
import os
from helpers import combineValueAndMultiplier
import json

# The path where the script will search for pcap files:
directory = 'local/pcaps_to_convert'

# stop the evaluation after this number of packets. Set to zero to have no limit.
nLimitNumberOfPackets = -1


def getManufacturerFromMAC(strMAC):
    # Examples based on https://macvendors.com/, and https://www.ipchecktool.com/tool/macfinder and own experience
    if (strMAC[0:5]=="ec:a2"):
        return "Kempower"
    if (strMAC[0:8]=="dc:44:27"):
        return "Tesla"
    if (strMAC[0:8]=="ce:25:1a"):
        return "Alpitronic"
    if (strMAC[0:8]=="1a:a9:8e"):
        return "Alpitronic"
    if (strMAC[0:8]=="e8:eb:1b"):
        return "Microchip (maybe ABB)"
    if (strMAC[0:8]=="68:27:19"):
        return "Microchip (maybe ABB)"
    if (strMAC[0:8]=="80:1f:12"):
        return "Microchip (maybe Compleo)"
    if (strMAC[0:5]=="18:d7"):
        return "(maybe Siemens)"
    return "(unknown vendor)"

# Examples of the decoder result:
#"EVSEPresentVoltage.Multiplier": "0",
#"EVSEPresentVoltage.Value": "318",
#"EVSEPresentVoltage.Unit": "V",
#"DC_EVStatus.EVRESSSOC": "53",

def convertPcapToTxt(inputFileName):
    global nLimitNumberOfPackets
    global directory
    cap = pyshark.FileCapture(inputFileName, display_filter="ipv6")
    fileOut = open(inputFileName + '.decoded.txt', 'w')
    print("# generated by pcapConverter.py", file=fileOut)
    print("# https://github.com/uhi22/pyPLC", file=fileOut)
    fileOutValues = open(inputFileName + '.values.txt', 'w')
    print("# generated by pcapConverter.py", file=fileOutValues)
    print("# https://github.com/uhi22/pyPLC", file=fileOutValues)
    fileOutStatistics = open(directory + '/pcap_statistics.txt', 'a')
    print("# statistics for " + inputFileName, file=fileOutStatistics)
    # Example how to access the data:
    #print(cap)
    #print(cap[0])
    #print(cap[1])
    #print(dir(cap[1]))
    #print(dir(cap[1].eth))
    #print(cap[1].eth.src) # the source MAC address
    #print(cap[1].sniff_time) # readable time
    #print(cap[1].sniff_timestamp) # epoch time
    t1CableCheckBegin = 0
    t2PreChargeBegin = 0
    t3CurrentDemandBegin = 0
    numberOfPackets=0
    decodeAlsoAsApplHandshake=0
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
                    #print(sHeader)
                    #print(decoded)
                    print(sHeader, file=fileOut)
                    print(decoded, file=fileOut)
                    if (decodeAlsoAsApplHandshake>0): # if it may be applHandShake, caused by the previous message, we decode also this.
                        print("Alternative decoding as applHandshake", file=fileOut)
                        decodeAlsoAsApplHandshake-=1
                        decoded=exiConnector.exiDecode(strExi, "DH")
                        print(decoded, file=fileOut)
                    if (decoded.find("error-")>0): # a decoding error usually points to wrong protocol, so most likely it is appHandShake.
                        print("maybe this is no DIN. Trying to decode as applHandshake", file=fileOut)
                        decodeAlsoAsApplHandshake=1
                        decoded=exiConnector.exiDecode(strExi, "DH")
                        print(decoded, file=fileOut)
                    if (decoded.find("SessionSetupReq")>0):
                        if ((t1CableCheckBegin>0) and (t2PreChargeBegin>t1CableCheckBegin) and (t3CurrentDemandBegin>t2PreChargeBegin)):
                            print("charger MAC " + chargerMAC + " " + getManufacturerFromMAC(chargerMAC))
                            timeForCableCheck = t2PreChargeBegin - t1CableCheckBegin
                            timeForPreCharge = t3CurrentDemandBegin - t2PreChargeBegin
                            print("timeForCableCheck= " + ("%.3f" % timeForCableCheck))
                            print("timeForPreCharge= " + ("%.3f" % timeForPreCharge))
                            print(chargerMAC + ";" + getManufacturerFromMAC(chargerMAC) + ";" + \
                            "timeForCableCheck;" + ("%.3f" % timeForCableCheck) + ";" + \
                            "timeForPreCharge; " + ("%.3f" % timeForPreCharge), file=fileOutStatistics)
                        t1CableCheckBegin = 0
                        t2PreChargeBegin = 0
                        t3CurrentDemandBegin = 0
                    if (decoded.find("CableCheckReq")>0) and (t1CableCheckBegin==0):
                        t1CableCheckBegin = float(packet.sniff_timestamp)
                        chargerMAC = str(packet.eth.dst)
                    if (decoded.find("PreChargeReq")>0) and (t2PreChargeBegin==0):
                        t2PreChargeBegin = float(packet.sniff_timestamp)
                    if (decoded.find("CurrentDemandReq")>0) and (t3CurrentDemandBegin==0):
                        t3CurrentDemandBegin = float(packet.sniff_timestamp)
                    try:
                        jsondict = json.loads(decoded)
                        try:
                            u = combineValueAndMultiplier(jsondict["EVSEPresentVoltage.Value"], jsondict["EVSEPresentVoltage.Multiplier"])
                            print("[" + str(packet.sniff_time) + "] EVSEPresentVoltage=" + str(u), file=fileOutValues)
                            i = combineValueAndMultiplier(jsondict["EVSEPresentCurrent.Value"], jsondict["EVSEPresentCurrent.Multiplier"])
                            print("[" + str(packet.sniff_time) + "] EVSEPresentCurrent=" + str(i), file=fileOutValues)
                        except:
                            pass
                        try:
                            u = combineValueAndMultiplier(jsondict["EVTargetVoltage.Value"], jsondict["EVTargetVoltage.Multiplier"])
                            print("[" + str(packet.sniff_time) + "] EVTargetVoltage=" + str(u), file=fileOutValues)
                            i = combineValueAndMultiplier(jsondict["EVTargetCurrent.Value"], jsondict["EVTargetCurrent.Multiplier"])
                            print("[" + str(packet.sniff_time) + "] EVTargetCurrent=" + str(i), file=fileOutValues)
                        except:
                            pass
                        try:
                            soc = jsondict["DC_EVStatus.EVRESSSOC"]
                            print("[" + str(packet.sniff_time) + "] EVRESSSOC=" + str(soc), file=fileOutValues)
                        except:
                            pass
                    except:
                        pass
        if ((numberOfPackets % 100)==0):
            print(str(numberOfPackets) + " packets")
        if ((nLimitNumberOfPackets>0) and (numberOfPackets>=nLimitNumberOfPackets)):
            break
    # Statistics of the timing:
    #print("t1CableCheckBegin " + str(t1CableCheckBegin))
    #print("t2PreChargeBegin " + str(t2PreChargeBegin))
    #print("t3CurrentDemandBegin " + str(t3CurrentDemandBegin))
    if ((t1CableCheckBegin>0) and (t2PreChargeBegin>t1CableCheckBegin) and (t3CurrentDemandBegin>t2PreChargeBegin)):
        print("charger MAC " + chargerMAC + " " + getManufacturerFromMAC(chargerMAC))
        timeForCableCheck = t2PreChargeBegin - t1CableCheckBegin
        timeForPreCharge = t3CurrentDemandBegin - t2PreChargeBegin
        print("timeForCableCheck= " + ("%.3f" % timeForCableCheck))
        print("timeForPreCharge= " + ("%.3f" % timeForPreCharge))

        print(chargerMAC + ";" + getManufacturerFromMAC(chargerMAC) + ";" + \
        "timeForCableCheck;" + ("%.3f" % timeForCableCheck) + ";" + \
        "timeForPreCharge; " + ("%.3f" % timeForPreCharge), file=fileOutStatistics)

    fileOutStatistics.close()
    fileOut.close()
    fileOutValues.close()


# iterate over files in the directory
for filename in os.listdir(directory):
    strFileNameWithPath = os.path.join(directory, filename)
    # checking if it is a file
    if os.path.isfile(strFileNameWithPath):
        print(strFileNameWithPath)
        # check the file extension:
        if (strFileNameWithPath[-5:]==".pcap") or (strFileNameWithPath[-7:]==".pcapng"):
            print("Will decode " + strFileNameWithPath)
            convertPcapToTxt(strFileNameWithPath)
