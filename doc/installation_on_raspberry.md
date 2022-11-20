# Installation on Raspberry Pi

To try out, we use an old raspberry pi (first generation).

Install an image on a fresh 16GB SD card, using the Raspberry Pi Imager from https://www.raspberrypi.com/software/.
Surprise: The imager does not ask for the model of the Raspberry. It just works on the old model. Fine.

In the Imager, we enable the SSH, this makes it possible to work remote on the raspberry.

On PC, we install putty, so that we are able to open an remote shell.

Start putty and connect to the raspberry.

Install samba server on the raspberry, to be able to access the files from remote. https://www.elektronik-kompendium.de/sites/raspberry-pi/2007071.htm

Install wireshark
```
	sudo apt-get install wireshark
```
Choose "yes" for the question whether other users shall be able to trace network traffic.


Clone the two github repositories, and compile the OpenV2Gx EXI decoder/encoder:
```
	cd $home
	mkdir myprogs
	cd myprogs
	git clone http://github.com/uhi22/pyPlc
	git clone http://github.com/uhi22/OpenV2Gx
	cd OpenV2Gx/Release
	make
```
(this may take some minutes)
(In case you later change something in the code, use `make all` to build again.)

Test the EXI decoder/encoder
```
	cd $home/myprogs/OpenV2Gx/Release
	./OpenV2G.exe DD809a0010d0400000c800410c8000
	./OpenV2G.exe EDB_5555aaaa5555aaaa
```
This should run without error and show the decoded/encoded data in the command window.

Now we go to the python part.
```
	cd $home/myprogs/pyPlc
```

Check python version

`python --version`
reports e.g. 3.9.2.

Install the python library for accessing the network interface.
Also for the superuser (otherwise the import pcap fails).

```
	python -m pip install --upgrade pcap-ct
	sudo python -m pip install --upgrade pcap-ct
```

Try-out whether the python is able to sniff ethernet packets:
```
	cd $home/myprogs/pyPlc/tests
	python test_pcap.py
```
Result: Fails due to missing permission. This is normal, we need to run with superuser permissions.
```
	sudo python test_pcap.py
```
This should run through loops 0 to 9.

Try-out the cooperation of Python with the EXI encoder/decoder:
```
	python exiConnector.py
```
This should run some decoder/encoder tests and report in the end "Number of fails: 0".


Start the EVSE `sudo python pyPlc.py E`.
Open a second console window, and start here the pev in simulation mode
`sudo python pyPlc.py P S`.
We should see how the EVSE and PEV are talking to each other.


