import pcap


print("Interfaces:\n" + '\n'.join(pcap.findalldevs()))
print("ex_name")
for i in range(0, 10):
    strInterfaceName = pcap.ex_name("eth"+str(i))
    if (strInterfaceName == '\\Device\\NPF_{E4B8176C-8516-4D48-88BC-85225ABCF259}'):
        print("This is the wanted Ethernet adaptor.")
    print("eth"+ str(i) + " is " + strInterfaceName)
    
sniffer = pcap.pcap(name=None, promisc=True, immediate=True, timeout_ms=50)
addr = lambda pkt, offset: '.'.join(str(pkt[i]) for i in range(offset, offset + 4))
for ts, pkt in sniffer:
     print('%d\tSRC %-16s\tDST %-16s' % (ts, addr(pkt, sniffer.dloff + 12), addr(pkt, sniffer.dloff + 16)))
