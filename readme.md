# Some try-outs with Python and network adaptor low-level communiation

## Goal
This project tries to use cheap powerline network adaptors for communication with electric cars charging system.

There are three different use cases, where this project can be helpful:
1. Sniffing the traffic between an CCS charger and a car. For instance to measure which side is the limiting element for reduced charging power.
2. Building a charger for CCS or for AC with digital communication.
3. Building a charging unit for a car which does not support powerline communication.

## References
* [i] https://www.goingelectric.de/wiki/CCS-Technische-Details/
* [ii] https://openinverter.org/forum/viewtopic.php?p=37085#p37085

## Quick start / overview
- Modify a PLC adaptor hardware, that it runs on battery
- Modify the configuration of the PLC adaptor, that it supports HomePlug Green Phy including the SLAC.
- Install wireshark to view the network traffic
- Install Pcap-ct python library
- Patch Pcap-ct to support non-blocking operation

## Hardware preparation
Tested device: TPlink TL-PA1040P Ver 5.0
- remove the housing
- remove the AC power connector parts
- connect cables to supply the device by battery. Works with 12V, also works with 5V from an USB power bank.
- connect cables and circuit (1nF and 150ohms in series) for connecting to the pilot line.

## Configuration of the PLC adaptor
The factory settings of the Homeplug PLC adaptor do not in all cases support the requirements of the communication
with the car. In detail, the adaptors are supporting HomePlugAV, but we need HomePlugGP (Green Phy). This is similar,
but not the same.
Fortunately, the supplier of the chipset is aware of this topic, and provides some smart helper tools.
http://github.com/qca/open-plc-utils
It is worth to read its documentation, starting in docbook/index.html, this contains all what we need for the next steps.

(Tested on Linux/Raspbian on a raspberryPi 3)

Find the PLC adaptor
```
	pi@RPi3D:~ $ int6klist -ieth0 -v
```
This shows the software version and the mac address.

Read the configuration from the PLC adaptor and write it to a file
```
	pi@RPi3D:~ $ plctool -ieth0 -p original.pib  98:48:27:5A:3C:E6
	eth0 98:48:27:5A:3C:E6 Read Module from Memory
```
Patch the configuration file (aee /docbook/ch05s15.html). For each side (pev (vehicle) and evse (charger)) there is a special configuration.
Example pev side:
```
	pi@RPi3D:~ $ cp original.pib pev.pib
	pi@RPi3D:~ $ setpib pev.pib 74 hfid "PEV"
	pi@RPi3D:~ $ setpib pev.pib F4 byte 1
	pi@RPi3D:~ $ setpib pev.pib 1653 byte 1
	pi@RPi3D:~ $ setpib pev.pib 1C98 long 10240 long 102400
```
Write the configuration file to the PLC adaptor
```
	pi@RPi3D:~ $ plctool -ieth0 -P pev.pib  98:48:27:5A:3C:E6
	eth0 98:48:27:5A:3C:E6 Start Module Write Session
	eth0 98:48:27:5A:3C:E6 Flash pev.pib
	...
	eth0 98:48:27:5A:3C:E6 Close Session
	eth0 98:48:27:5A:3C:E6 Reset Device
	eth0 98:48:27:5A:3C:E6 Resetting ...
```
The open-plc-utils contain the programs evse and pev, which can be used for try-out of the functionality, using two PLC adaptors. 

## Installation / Preconditions on PC side
### Usage on Windows10

1.	Install python (windows automatically launches the installer if you type „python“ into the search field of the task bar)
2.	Wireshark is already installed, this includes the pcap driver, which is necessary for low-level-network-interaction

Attention: There are (at least) three different python-libs available for pcap:
-	Libpcap
-	Pylibpcap (But: only Python2)
-	Pypcap (recommented on https://stackoverflow.com/questions/63941109/pcap-open-live-issue)
-	Pcap-ct (https://pypi.org/project/pcap-ct/)
We use the last one.
	python -m pip install --upgrade pcap-ct
This is fighting against the Libpcap-installation, so we need to deinstall the second:
	python -m pip uninstall libpcap
Then again install pcap-ct, and finally add in the libpcap\_platform\__init__py the missing is_osx = False. (Is in the meanwhile fixed in the github repository.)

Finally, we need to patch the Pcap-ct, because the python script needs a non-blocking version. This is discussed in https://github.com/karpierz/pcap-ct/issues/9

Now, in the IDLE shall 3.10.6, the import works:
```
	import pcap
	sniffer = pcap.pcap(name=None, promisc=True, immediate=True, timeout_ms=50)
	addr = lambda pkt, offset: '.'.join(str(pkt[i]) for i in range(offset, offset + 4))
	for ts, pkt in sniffer:
		print('%d\tSRC %-16s\tDST %-16s' % (ts, addr(pkt, sniffer.dloff + 12), addr(pkt, sniffer.dloff + 16)))
```

### Usage on Raspberry
Pcap-ct does not work with Python 3.4. After update to Python 3.8, it works.


## Change history / functional status
### 2022-10-19 Communication with Ioniq car established
* Using a TPlink TL-PA4010P with firmware MAC-QCA7420-1.4.0.20-00-20171027-CS and the PIB configuration file patched for evse according to the open-plc-utils docu.
* Python software running on Win10, Python 3.10.8
* On control pilot, sending 5% PWM to initiate digital communication with the car
* Since the TPlink is configured as coordinator, it sends "alive" messages, and the IONIQ starts sending the SLAC_PARAM.REQ.
* Per keystroke, we trigger a SET_KEY before the car is connected. The TPlink responds with "rejected", but this is normal, the LEDs are turning off and on, key is accepted.
* Python script interprets the relevant incoming messages (SLAC_PARAM.REQ, MNBC_SOUND.IND, SLAC_MATCH.REQ) and reacts accordingly.
* After successfull SLAC sequence, all three LEDs on the TPlink are ON, means: Network is established.
* In wireshark, we see that the car is sending UDP multicast messages to destination port 15118. This looks like a good sign, that it wants a ISO15118 compatible communication.
![image](https://user-images.githubusercontent.com/98478946/196766285-1c3152f7-31db-4b5f-98b1-9f1216f9b9de.png)

### 2022-10-19 Sniffing mode not yet working with the TPlink adaptors
* with a Devolo dLAN 200 AVplus, software INT6000-MAC-4-4-4405-00-4497-20101201-FINAL-B in original parametrization, it is possible
to see the complete SLAC traffic (both directions) which sniffing the communication between a real charger and a real car. This does
NOT work with the TPlink adaptors. They route only "their own" direction of the traffic to the ethernet. Means: The pev-configured device
does not see the real car, and the evse-configured device does not see the real charger. This is bad for sniffing.


(further steps ongoing)
