
# Preconditions:
# Library pcap-ct (not libpcap, not pylibpcap, not pypcap)
#
# Version 2022-08-14:
#  - Selection of interfaces ok
#  - Sniffing of the SLAC-request ok
#  - Transmission of a demo message ok
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


class pyPlcHomeplug():    
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

    def composeTestFrameSlacReq(self):
		# SLAC request, as it was recorded 2021-12-17 WP charger 2
        self.mytransmitbuffer = bytearray(60)
        # Destination MAC
        self.mytransmitbuffer[0]=0xFF
        self.mytransmitbuffer[1]=0xFF
        self.mytransmitbuffer[2]=0xFF
        self.mytransmitbuffer[3]=0xFF
        self.mytransmitbuffer[4]=0xFF
        self.mytransmitbuffer[5]=0xFF

        # Source MAC
        self.mytransmitbuffer[6]=0x04 # Ioniq MAC
        self.mytransmitbuffer[7]=0x65
        self.mytransmitbuffer[8]=0x65
        self.mytransmitbuffer[9]=0x00
        self.mytransmitbuffer[10]=0x64
        self.mytransmitbuffer[11]=0xC3

        # Protocol
        self.mytransmitbuffer[12]=0x88 # Protocol HomeplugAV
        self.mytransmitbuffer[13]=0xE1

        self.mytransmitbuffer[14]=0x01 # version
        self.mytransmitbuffer[15]=0x64 # SLAC_PARAM.REQ

        self.mytransmitbuffer[16]=0x60 # 
        self.mytransmitbuffer[17]=0x00 # 
        self.mytransmitbuffer[18]=0x00 # 
        self.mytransmitbuffer[19]=0x00 # 
        self.mytransmitbuffer[20]=0x00 # 
        self.mytransmitbuffer[21]=0x04 # runid 8 bytes
        self.mytransmitbuffer[22]=0x65 # 
        self.mytransmitbuffer[23]=0x65 # 
        self.mytransmitbuffer[24]=0x00 # 
        self.mytransmitbuffer[25]=0x64 # 
        self.mytransmitbuffer[26]=0xC3 # 
        self.mytransmitbuffer[27]=0x00 # 
        self.mytransmitbuffer[28]=0x00 # 
        
        self.mytransmitbuffer[29]=0x00 # rest is 0
        self.mytransmitbuffer[30]=0x00 # 
        self.mytransmitbuffer[31]=0x00 # 
        self.mytransmitbuffer[32]=0x00 # 
        self.mytransmitbuffer[33]=0x00 # 
        self.mytransmitbuffer[34]=0x00 # 
        self.mytransmitbuffer[35]=0x00 # 
        self.mytransmitbuffer[36]=0x00 # 
        self.mytransmitbuffer[37]=0x00 # 
        self.mytransmitbuffer[38]=0x00 # 
        self.mytransmitbuffer[39]=0x00 # 
        self.mytransmitbuffer[40]=0x00 # 
        self.mytransmitbuffer[41]=0x00 # 
        self.mytransmitbuffer[42]=0x00 # 
        self.mytransmitbuffer[43]=0x00 # 
        self.mytransmitbuffer[44]=0x00 # 
        self.mytransmitbuffer[45]=0x00 # 
        self.mytransmitbuffer[46]=0x00 # 
        self.mytransmitbuffer[47]=0x00 #
        self.mytransmitbuffer[48]=0x00 # 
        self.mytransmitbuffer[49]=0x00 # 
        self.mytransmitbuffer[50]=0x00 # 
        self.mytransmitbuffer[51]=0x00 # 
        self.mytransmitbuffer[52]=0x00 # 
        self.mytransmitbuffer[53]=0x00 # 
        self.mytransmitbuffer[54]=0x00 # 
        self.mytransmitbuffer[55]=0x00 # 
        self.mytransmitbuffer[56]=0x00 # 
        self.mytransmitbuffer[57]=0x00 # 
        self.mytransmitbuffer[58]=0x00 # 
        self.mytransmitbuffer[59]=0x00 # 

    def composeTestFrameSlacResp(self):
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
        self.addToTrace("transmitting test frame...")
        self.composeTestFrameSlacReq()
        self.sniffer.sendpacket(bytes(self.mytransmitbuffer))
        
    def findEthernetAdaptor(self):
        self.strInterfaceName="eth0" # default, if the real is not found
        print("Interfaces:\n" + '\n'.join(pcap.findalldevs()))
        for i in range(0, 10):
            strInterfaceName = pcap.ex_name("eth"+str(i))
            if (strInterfaceName == '\\Device\\NPF_{E4B8176C-8516-4D48-88BC-85225ABCF259}'):
                print("This is the wanted Ethernet adaptor.")
                self.strInterfaceName="eth"+str(i)
            print("eth"+ str(i) + " is " + strInterfaceName)

    def __init__(self, callbackAddToTrace=None, callbackShowStatus=None):
        self.mytransmitbuffer = bytearray("Hallo das ist ein Test", 'UTF-8')
        self.nPacketsReceived = 0
        self.callbackAddToTrace = callbackAddToTrace
        self.callbackShowStatus = callbackShowStatus
        #self.sniffer = pcap.pcap(name=None, promisc=True, immediate=True, timeout_ms=50)
        # eth3 means: Third entry from back, in the list of interfaces, which is provided by pcap.findalldevs.
        #  Improvement necessary: select the interface based on the name.
        # For debugging of the interface names, we can patch the file
        # C:\Users\uwemi\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\LocalCache\local-packages\Python310\site-packages\pcap\_pcap_ex.py,
        # in the function
        #    def name(name: bytes) -> bytes:
        # in the place after
        # if i == idx:
        #           print("index match at " + str(i) + " dev name=" + str(dev.name) + " dev.description=" + str(dev.description))
        # This will print the description of the used interface.
        #
        # Patch for non-blocking read-iteration:
        #   in _pcap.py, function def __next__(self), in the case of timeout (if n==0), we need to "raise StopIteration" instead of "continue".
        #
        self.findEthernetAdaptor()
        self.sniffer = pcap.pcap(name=self.strInterfaceName, promisc=True, immediate=True, timeout_ms=50)
        self.sniffer.setnonblock(True)
        print("sniffer created at " + self.strInterfaceName)

    def addToTrace(self, s):
        self.callbackAddToTrace(s)

    def showStatus(self, s):
        self.callbackShowStatus(s) 
        
    def mainfunction(self):  
        # print("will evaluate self.sniffer")
        for ts, pkt in self.sniffer: # attention: for using this in non-blocking manner, we need the patch described above.
            self.nPacketsReceived+=1
            print('%d' % (ts))
            #if (self.isHomeplug(pkt)):
            #    self.showMacAddresses(pkt)
            #    showAsHex(pkt)
            #    if (pkt[15]==0x64): #SLAC_Request
            #        self.sendTestFrame()
            #    
            #else:
            #    addToTrace("(other)")
        self.showStatus("nPacketsReceived=" + str(self.nPacketsReceived))
        
    def close(self):
        self.sniffer.close()

#sn = pyPlcHomeplug()
#while (1):
# print("Press control-C to stop")
# sn.mainfunction()
