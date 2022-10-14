# Some try-outs with Python and network adaptor low-level communiation

## Installation / Preconditions
Tested with windows10

1.	Install python (windows automatically launches the installer if you type „python“ into the search field of the task bar)
2.	Wireshark is already installed, this includes the pcap driver, which is necessary for low-level-network-interaction

Attention: There are (at least) three different python-libs available for pcap:
-	Libpcap
-	Pylibpcap (But: only Python2)
-	Pypcap (recommented on https://stackoverflow.com/questions/63941109/pcap-open-live-issue)
-	Pcap-ct (https://pypi.org/project/pcap-ct/)

python -m pip install --upgrade pcap-ct
This is fighting against the Libpcap-installation, so we need to deinstall the second:
python -m pip uninstall libpcap
Then again install pcap-ct, and finally add in the libpcap\_platform\__init__py the missing is_osx     = False.

Now, in the IDLE shall 3.10.6, the import works:
import pcap
sniffer = pcap.pcap(name=None, promisc=True, immediate=True, timeout_ms=50)
addr = lambda pkt, offset: '.'.join(str(pkt[i]) for i in range(offset, offset + 4))
for ts, pkt in sniffer:
     print('%d\tSRC %-16s\tDST %-16s' % (ts, addr(pkt, sniffer.dloff + 12), addr(pkt, sniffer.dloff + 16)))

## Test image
(Just added in the Github web interface while editing the readme.md, by pressing Ctrl-V)
![image](https://user-images.githubusercontent.com/98478946/194760396-11c36e78-fed3-4d07-87ff-c7d2649a41b2.png)

## Further steps
(to be continued)
