
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


class uwe_sniffer():    
    def showIpAddresses(self, mybytearray):
        addr = lambda pkt, offset: '.'.join(str(pkt[i]) for i in range(offset, offset + 4))
        print('SRC %-16s\tDST %-16s' % (addr(mybytearray, self.sniffer.dloff + 12), addr(mybytearray, self.sniffer.dloff + 16)))

    def showMacAddresses(self, mybytearray):
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

    def isHomeplug(self, mybytearray):
        blIsHomePlug=False
        if len(mybytearray)>(6+6+2):
            protocol=mybytearray[12]*256 + mybytearray[13]
            if (protocol == 0x88E1):
                blIsHomePlug=True
                print("HomePlug protocol")
        return blIsHomePlug

    def composeTestFrame(self):
        self.mytransmitbuffer = bytearray(60)
        # Destination MAC
        self.mytransmitbuffer[0]=0x04 # Ioniq MAC
        self.mytransmitbuffer[1]=0x65
        self.mytransmitbuffer[2]=0x65
        self.mytransmitbuffer[3]=0x00
        self.mytransmitbuffer[4]=0x64
        self.mytransmitbuffer[5]=0xC3

        # Source MAC
        self.mytransmitbuffer[6]=0x0A # Alpi MAC
        self.mytransmitbuffer[7]=0x19
        self.mytransmitbuffer[8]=0x4A
        self.mytransmitbuffer[9]=0x39
        self.mytransmitbuffer[10]=0xD6
        self.mytransmitbuffer[11]=0x98

        # Protocol
        self.mytransmitbuffer[12]=0x88 # Protocol HomeplugAV
        self.mytransmitbuffer[13]=0xE1

        self.mytransmitbuffer[14]=0x01 # version
        self.mytransmitbuffer[15]=0x65 # SLAC_PARAM.confirm

        self.mytransmitbuffer[16]=0x60 # 
        self.mytransmitbuffer[17]=0x00 # 
        self.mytransmitbuffer[18]=0x00 # 
        self.mytransmitbuffer[19]=0xff # 
        self.mytransmitbuffer[20]=0xff # 
        self.mytransmitbuffer[21]=0xff # 
        self.mytransmitbuffer[22]=0xff # 
        self.mytransmitbuffer[23]=0xff # 
        self.mytransmitbuffer[24]=0xff # 
        self.mytransmitbuffer[25]=0x0A # 
        self.mytransmitbuffer[26]=0x06 # 
        self.mytransmitbuffer[27]=0x01 # 
        self.mytransmitbuffer[28]=0x04 # 
        self.mytransmitbuffer[29]=0x65 # 
        self.mytransmitbuffer[30]=0x65 # 
        self.mytransmitbuffer[31]=0x00 # 

        self.mytransmitbuffer[32]=0x64 # 
        self.mytransmitbuffer[33]=0xC3 # 
        self.mytransmitbuffer[34]=0x00 # 
        self.mytransmitbuffer[35]=0x00 # 
        self.mytransmitbuffer[36]=0x04 # 
        self.mytransmitbuffer[37]=0x65 # 
        self.mytransmitbuffer[38]=0x65 # 
        self.mytransmitbuffer[39]=0x00 # 
        self.mytransmitbuffer[40]=0x64 # 
        self.mytransmitbuffer[41]=0xC3 # 
        self.mytransmitbuffer[42]=0x0 # 
        self.mytransmitbuffer[43]=0x0 # 
        self.mytransmitbuffer[44]=0x0 # 
        self.mytransmitbuffer[45]=0x0 # 
        self.mytransmitbuffer[46]=0x0 # 
        self.mytransmitbuffer[47]=0x0 #
 
        self.mytransmitbuffer[48]=0x0 # 
        self.mytransmitbuffer[49]=0x0 # 
        self.mytransmitbuffer[50]=0x0 # 
        self.mytransmitbuffer[51]=0x0 # 
        self.mytransmitbuffer[52]=0x0 # 
        self.mytransmitbuffer[53]=0x0 # 
        self.mytransmitbuffer[54]=0x0 # 
        self.mytransmitbuffer[55]=0x0 # 
        self.mytransmitbuffer[56]=0x0 # 
        self.mytransmitbuffer[57]=0x0 # 
        self.mytransmitbuffer[58]=0x0 # 
        self.mytransmitbuffer[59]=0x0 # 

    def sendTestFrame(self):
        print("transmitting...")
        self.composeTestFrame()
        self.sniffer.sendpacket(bytes(self.mytransmitbuffer))

    def init(self):
        self.mytransmitbuffer = bytearray("Hallo das ist ein Test", 'UTF-8')
        #self.sniffer = pcap.pcap(name=None, promisc=True, immediate=True, timeout_ms=50)
        # eth3 bedeutet: Dritter Eintrag von hinten, in der Liste der Interfaces, die von pcap.findalldevs geliefert wird.
        #  Verbesserungsbedarf: Interface namensbasiert auswählen.
        self.sniffer = pcap.pcap(name="eth3", promisc=True, immediate=True, timeout_ms=50)
    def runEndless(self):
        print("Press control-C to stop")
        for ts, pkt in self.sniffer:
            #print('%d' % (ts))
            if (self.isHomeplug(pkt)):
                self.showMacAddresses(pkt)
                showAsHex(pkt)
                if (pkt[15]==0x64): #SLAC_Request
                    self.sendTestFrame()
                
            else:
                print("(other)")
    def close(self):
        self.sniffer.close()

sn = uwe_sniffer()
sn.init()
sn.runEndless()