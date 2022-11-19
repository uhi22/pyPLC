
# test 

import pcap
import time


 
class tester():    
            
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
        self.sniffer = pcap.pcap(name=self.strInterfaceName, promisc=True, immediate=True, timeout_ms=10)
        self.sniffer.setnonblock(True)
        print("sniffer created at " + self.strInterfaceName)
        
    def mainfunction(self):  
        # print("will evaluate self.sniffer")
        for ts, pkt in self.sniffer: # attention: for using this in non-blocking manner, we need the patch described above.
            self.nPacketsReceived+=1
            # print('%d' % (ts)) # the time stamp

    def callbackfunction(self, timestamp, pkt, *args):
        self.nPacketsReceived+=1
        #print("The callback #" + str(self.nPacketsReceived) + " " + str(len(pkt)) + " bytes:" + '%d' % (timestamp)) # the time stamp
        
    def mainfunction_new(self):
        # https://stackoverflow.com/questions/31305712/how-do-i-make-libpcap-pcap-loop-non-blocking
        # Tell the sniffer to give max 100 received packets to the callback function:
        self.sniffer.dispatch(100, self.callbackfunction, None)

    def close(self):
        self.sniffer.close()

t=tester()
for i in range(0, 10):
    print("Loop nr " + str(i) + " and " + str(t.nPacketsReceived) + " packets in total")
    time.sleep(0.01)
    t.mainfunction_new()
t.close()
