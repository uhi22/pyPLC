
# test 

import pcap
import time

MAC_BROADCAST = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF ]
MAC_LAPTOP    = [0xdc, 0x0e, 0xa1, 0x11, 0x67, 0x08 ]
MAC_RANDOM    = [0xaa, 0xbb, 0xcc, 0xdd, 0xee, 0xff ]
MAC_ALPI      = [0x0A, 0x19, 0x4A, 0x39, 0xD6, 0x98 ] # alpitronics
MAC_TPLINK_E4 = [0x98, 0x48, 0x27, 0x5A, 0x3C, 0xE4 ] # TPlink PLC adaptor
MAC_TPLINK_E6 = [0x98, 0x48, 0x27, 0x5A, 0x3C, 0xE6 ] # TPlink PLC adaptor
MAC_DEVOLO_26 = [0xBC, 0xF2, 0xAF, 0x0B, 0x8E, 0x26 ] # Devolo PLC adaptor
MAC_IPv6MCAST1 = [0x33, 0x33, 0x00, 0x00, 0x00, 0x01 ] # IPv6 multicast MAC
MAC_RANDCAR    = [0x04, 0x65, 0x65, 0x00, 0xaf, 0xfe ] # random hyundai car 

mac_test = [0xb8, 0x27, 0xeb, 0x27, 0x33, 0x50 ]
 
class tester():    
        
    def cleanTransmitBuffer(self): # fill the complete ethernet transmit buffer with 0x00
        for i in range(0, len(self.mytransmitbuffer)):
            self.mytransmitbuffer[i]=0
            
    def fillSourceMac(self, mac, offset=6): # at offset 6 in the ethernet frame, we have the source MAC
        # we can give a different offset, to re-use the MAC also in the data area
        for i in range(0, 6):
            self.mytransmitbuffer[offset+i]=mac[i]
        
    def fillDestinationMac(self, mac, offset=0): # at offset 0 in the ethernet frame, we have the destination MAC
         # we can give a different offset, to re-use the MAC also in the data area
        for i in range(0, 6):
            self.mytransmitbuffer[offset+i]=mac[i]
            
    def sendTestFrame1(self):
        self.mytransmitbuffer = bytearray(72)
        self.cleanTransmitBuffer()
        # Destination MAC
        self.fillDestinationMac(MAC_IPv6MCAST1)
        # Source MAC
        self.fillSourceMac(MAC_RANDCAR)
        # Protocol
        self.mytransmitbuffer[12]=0x86 # IPv6
        self.mytransmitbuffer[13]=0xdd
        self.mytransmitbuffer[14]=0x60 # 
        self.mytransmitbuffer[15]=0x00 #
        self.mytransmitbuffer[16]=0x00 #
        self.mytransmitbuffer[17]=0x00 # 

        self.mytransmitbuffer[18]=0x00 # len 2 bytes
        self.mytransmitbuffer[19]=0x12 #
        
        self.mytransmitbuffer[20]=0x11 # next is UDP
        self.mytransmitbuffer[21]=0x0A # hop limit

        self.mytransmitbuffer[22]=0xfe        # 22 to 37 ip source address
        self.mytransmitbuffer[23]=0x80        # 22 to 37 ip source address
        self.mytransmitbuffer[24]=0x00        # 22 to 37 ip source address
        self.mytransmitbuffer[25]=0x00        # 22 to 37 ip source address
        self.mytransmitbuffer[26]=0x00        # 22 to 37 ip source address
        self.mytransmitbuffer[27]=0x00        # 22 to 37 ip source address
        self.mytransmitbuffer[28]=0x00        # 22 to 37 ip source address
        self.mytransmitbuffer[29]=0x00        # 22 to 37 ip source address
        self.mytransmitbuffer[30]=0x06        # 22 to 37 ip source address
        self.mytransmitbuffer[31]=0x65        # 22 to 37 ip source address
        self.mytransmitbuffer[32]=0x65        # 22 to 37 ip source address
        self.mytransmitbuffer[33]=0xff        # 22 to 37 ip source address
        self.mytransmitbuffer[34]=0xfe        # 22 to 37 ip source address
        self.mytransmitbuffer[35]=0x00        # 22 to 37 ip source address
        self.mytransmitbuffer[36]=0x64        # 22 to 37 ip source address
        self.mytransmitbuffer[37]=0xc3        # 22 to 37 ip source address
        
        self.mytransmitbuffer[38]=0xff        # 38 to 53 ip destination address
        self.mytransmitbuffer[39]=0x02        # 38 to 53 ip destination address
        self.mytransmitbuffer[53]=0x01        # 38 to 53 ip destination address

        self.mytransmitbuffer[54]=0xcc   # source port
        self.mytransmitbuffer[55]=0xab

        self.mytransmitbuffer[56]=0x3b # dest port
        self.mytransmitbuffer[57]=0x0e
        
        self.mytransmitbuffer[58]=0x00 # length
        self.mytransmitbuffer[59]=0x12
        
        self.mytransmitbuffer[60]= 0x89 # checksum
        self.mytransmitbuffer[61]= 0x62

        self.mytransmitbuffer[62]= 0x01
        self.mytransmitbuffer[63]= 0xFE
        
        self.mytransmitbuffer[64]= 0x90
        self.mytransmitbuffer[65]= 0x00
        
        self.mytransmitbuffer[66]= 0x00
        self.mytransmitbuffer[67]= 0x00
        self.mytransmitbuffer[68]= 0x00
        self.mytransmitbuffer[69]= 0x02
        
        self.mytransmitbuffer[70]= 0x10
        self.mytransmitbuffer[71]= 0x00
                      
        self.sniffer.sendpacket(bytes(self.mytransmitbuffer))
        print("transmitted test frame 1")

    def sendTestFrame2(self):
        self.mytransmitbuffer = bytearray(72)
        self.cleanTransmitBuffer()
        # Destination MAC
        self.fillDestinationMac(MAC_IPv6MCAST1)
        # Source MAC
        self.fillSourceMac(mac_test)
        # Protocol
        self.mytransmitbuffer[12]=0x86 # IPv6
        self.mytransmitbuffer[13]=0xdd
        self.mytransmitbuffer[14]=0x60 # 
        self.mytransmitbuffer[15]=0x00 #
        self.mytransmitbuffer[16]=0x00 #
        self.mytransmitbuffer[17]=0x00 # 

        self.mytransmitbuffer[18]=0x00 # len 2 bytes
        self.mytransmitbuffer[19]=0x12 #
        
        self.mytransmitbuffer[20]=0x11 # next is UDP
        self.mytransmitbuffer[21]=0x0A # hop limit

        self.mytransmitbuffer[22]=0xfe        # 22 to 37 ip source address
        self.mytransmitbuffer[23]=0x80        # 22 to 37 ip source address
        self.mytransmitbuffer[24]=0x00        # 22 to 37 ip source address
        self.mytransmitbuffer[25]=0x00        # 22 to 37 ip source address
        self.mytransmitbuffer[26]=0x00        # 22 to 37 ip source address
        self.mytransmitbuffer[27]=0x00        # 22 to 37 ip source address
        self.mytransmitbuffer[28]=0x00        # 22 to 37 ip source address
        self.mytransmitbuffer[29]=0x00        # 22 to 37 ip source address
        self.mytransmitbuffer[30]=0x06        # 22 to 37 ip source address
        self.mytransmitbuffer[31]=0x65        # 22 to 37 ip source address
        self.mytransmitbuffer[32]=0x65        # 22 to 37 ip source address
        self.mytransmitbuffer[33]=0xff        # 22 to 37 ip source address
        self.mytransmitbuffer[34]=0xfe        # 22 to 37 ip source address
        self.mytransmitbuffer[35]=0x00        # 22 to 37 ip source address
        self.mytransmitbuffer[36]=0x64        # 22 to 37 ip source address
        self.mytransmitbuffer[37]=0xc3        # 22 to 37 ip source address
        
        self.mytransmitbuffer[38]=0xff        # 38 to 53 ip destination address
        self.mytransmitbuffer[39]=0x02        # 38 to 53 ip destination address
        self.mytransmitbuffer[53]=0x01        # 38 to 53 ip destination address

        self.mytransmitbuffer[54]=0xcc   # source port
        self.mytransmitbuffer[55]=0xab

        self.mytransmitbuffer[56]=0x3b # dest port
        self.mytransmitbuffer[57]=0x0e
        
        self.mytransmitbuffer[58]=0x00 # length
        self.mytransmitbuffer[59]=0x12
        
        self.mytransmitbuffer[60]= 0x89 # checksum
        self.mytransmitbuffer[61]= 0x62

        self.mytransmitbuffer[62]= 0x01
        self.mytransmitbuffer[63]= 0xFE
        
        self.mytransmitbuffer[64]= 0x90
        self.mytransmitbuffer[65]= 0x00
        
        self.mytransmitbuffer[66]= 0x00
        self.mytransmitbuffer[67]= 0x00
        self.mytransmitbuffer[68]= 0x00
        self.mytransmitbuffer[69]= 0x02
        
        self.mytransmitbuffer[70]= 0x10
        self.mytransmitbuffer[71]= 0x00
                      
        self.sniffer.sendpacket(bytes(self.mytransmitbuffer))
        print("transmitted test frame 2")

            
            
    def findEthernetAdaptor(self):
        self.strInterfaceName="eth0" # default, if the real is not found
        print("Interfaces:\n" + '\n'.join(pcap.findalldevs()))
        for i in range(0, 10):
            strInterfaceName = pcap.ex_name("eth"+str(i))
            if (strInterfaceName == '\\Device\\NPF_{E4B8176C-8516-4D48-88BC-85225ABCF259}'):
                print("This is the wanted Ethernet adaptor.")
                self.strInterfaceName="eth"+str(i)
            print("eth"+ str(i) + " is " + strInterfaceName)
            

    def __init__(self):
        self.mytransmitbuffer = bytearray("Hallo das ist ein Test", 'UTF-8')
        self.nPacketsReceived = 0
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
        
    def mainfunction(self):  
        # print("will evaluate self.sniffer")
        for ts, pkt in self.sniffer: # attention: for using this in non-blocking manner, we need the patch described above.
            self.nPacketsReceived+=1
            # print('%d' % (ts)) # the time stamp

    def close(self):
        self.sniffer.close()

t=tester()
print(256 ** 2)
for i in range(0, 1000):
    t.sendTestFrame2()
    mac_test[5]+=1
    if (mac_test[5]>255):
        mac_test[5]=0
        mac_test[4]+=1
        if (mac_test[4]>255):
            mac_test[4]=0
    time.sleep(0.01)
t.close()
