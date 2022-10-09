
# Vorraussetzungen:
# Library pcap-ct (nicht libpcap, nicht pylibpcap, nicht pypcap)
#
# Stand 2022-08-14:
#  - Auswahl des Interaces ok
#  - Sniffen des SLAC-request ok
#  - Aussenden eine Demo-Botschaft ok
#
import pcap

def twoCharHex(b):
    strHex = "%0.2X" % b
    return strHex
    
def showAsHex(mybytearray):
    packetlength = len(mybytearray)
    strHex = ""
    for i in range(0, packetlength):
        strHex = strHex + twoCharHex(mybytearray[i]) + " "
    print("len " + str(packetlength) + " data " + strHex)

def showIpAddresses(mybytearray):
    addr = lambda pkt, offset: '.'.join(str(pkt[i]) for i in range(offset, offset + 4))
    print('SRC %-16s\tDST %-16s' % (addr(mybytearray, sniffer.dloff + 12), addr(mybytearray, sniffer.dloff + 16)))

def showMacAddresses(mybytearray):
    strDestMac = ""
    for i in range(0, 6):
        strDestMac = strDestMac + twoCharHex(mybytearray[i]) + ":"
    strSourceMac = ""
    for i in range(5, 12):
        strSourceMac = strSourceMac + twoCharHex(mybytearray[i]) + ":"
    lastThreeOfSource = mybytearray[6]*256*256 + mybytearray[7]*256 + mybytearray[8]
    strSourceFriendlyName = ""
    if (lastThreeOfSource == 0x0a663a):
        strSourceFriendlyName="Fritzbox"
    if (lastThreeOfSource == 0x0064c3):
        strSourceFriendlyName="Ioniq"
        
    print("From " + strSourceMac + strSourceFriendlyName + " to " + strDestMac)

def isHomeplug(mybytearray):
    blIsHomePlug=False
    if len(mybytearray)>(6+6+2):
        protocol=mybytearray[12]*256 + mybytearray[13]
        if (protocol == 0x88E1):
            blIsHomePlug=True
            print("HomePlug protocol")
    return blIsHomePlug

def sendTestFrame():
    print("todo...")

mytransmitbuffer = bytearray("Hallo das ist ein Test", 'UTF-8')
    
#sniffer = pcap.pcap(name=None, promisc=True, immediate=True, timeout_ms=50)
# eth3 bedeutet: Dritter Eintrag von hinten, in der Liste der Interfaces, die von pcap.findalldevs geliefert wird.
#  Verbesserungsbedarf: Interface namensbasiert auswählen.
sniffer = pcap.pcap(name="eth3", promisc=True, immediate=True, timeout_ms=50)
print("Press control-C to stop")
for ts, pkt in sniffer:
    #print('%d' % (ts))
    if (isHomeplug(pkt)):
        showMacAddresses(pkt)
        showAsHex(pkt)        
        sendTestFrame()
        sniffer.sendpacket(bytes(mytransmitbuffer))
    else:
        print("(other)")

sniffer.close()