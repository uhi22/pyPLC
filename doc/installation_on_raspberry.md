# Installation on Raspberry Pi

To try out, we use an old raspberry pi (first generation).

Install an image on a fresh 16GB SD card, using the Raspberry Pi Imager from https://www.raspberrypi.com/software/.
Surprise: The imager does not ask for the model of the Raspberry. It just works on the old model. Fine.

In the Imager, we enable the SSH, this makes it possible to work remote on the raspberry.

On PC, we install putty, so that we are able to open an remote shell.

Start putty and connect to the raspberry.

Install samba server on the raspberry, to be able to access the files from remote. https://www.elektronik-kompendium.de/sites/raspberry-pi/2007071.htm

Install wireshark
sudo apt-get install wireshark
Choose "yes" for the question whether other users shall be able to trace network traffic.

cd $home
mkdir myprogs
cd myprogs

git clone http://github.com/uhi22/pyPlc

git clone http://github.com/uhi22/OpenV2Gx
cd OpenV2Gx/Release
make

Test the EXI decoder/encoder
./OpenV2G DD809a0010d0400000c800410c8000
./OpenV2G EDa

cd $home/myprogs/pyPlc

Check python version
python --version
reports e.g. 3.9.2.

Install the python library for accessing the network interface:
python -m pip install --upgrade pcap-ct
also for the superuser (otherwise the import pcap fails)
sudo python -m pip install --upgrade pcap-ct

Try-out whether the python is able to sniff ethernet packets:
cd $home/myprogs/pyPlc/tests
python test_pcap.py
Result: Fails due to missing permission. This is normal, we need to run with superuser permissions.
sudo python test_pcap.py
This should run through loops 0 to 9. If it stucks at Loop 0, the
patch for non-blocking is missing.

Patch is not needed if we use self.sniffer.dispatch.

Patch the pcap-ct for non-blocking usage:
Navigate to /usr/local/lib/python3.9/dist-packages/pcap
cd /usr/local/lib/python3.9/dist-packages/pcap
Open the file _pcap.py with superuser permissions:
sudo nano _pcap.py
Scroll to "def __next__".
Under the condition "if n == 0: # timeout" replace the line
continue
by
raise StopIteration
This issue is discussed in https://github.com/karpierz/pcap-ct/issues/9.

Try again
sudo python test_pcap.py
This should run through loops 0 to 9.

Problem: Each loop needs around 2 seconds. This is not intended. The 10ms timeout
seems not to work (timeout_ms=10). On win10, this works perfect.
On Raspberry, the combination of iterator and non-blocking does not work, see
https://stackoverflow.com/questions/31305712/how-do-i-make-libpcap-pcap-loop-non-blocking.
Solution: Change to self.sniffer.dispatch instead of for ts, pkt in self.sniffer.


