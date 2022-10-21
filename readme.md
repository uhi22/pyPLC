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

## Example flow
This chapter describes the start of a charging session, considering all layers.

Precondition: On charger side, there is a homeplugGP-capable device present, which is configured as CentralCoordinator.
1. The charger creates a "random" value for NID (network ID) and NMK (network membership key), and configures its homeplug modem with these values.
1. The charger provides 12V on the control pilot (CP) line (State A).
1. The user connects the plug into the car.
2. The car pulls the 12V at CP line to 9V (State B).
3. The charger sees the level change on CP and applies 5% PWM on CP.
4. The car sees the 5%, and interprets it as request for digital communication. It wakes up its communication controller and homeplug modem.
5. The car sees homeplug coordinator packets on the CP, and starts the SLAC sequence by sending SLAC_PARAM.REQ. Can be also two times.
6. The charger receives the SLAC_PARAM.REQ and confirms it with SLAC_PARAM.CNF.
7. The car sends START_ATTEN_CHAR.IND, to start the attenuation measurement. In total 3 times.
8. The car sends MNBC_SOUND.IND, to provide different sounds. In total 10 times.
8. The homeplug modem in the charger should measure the signal strength, and report the values to the SECC in an ethernet frame ATTEN_PROFILE.IND.
However, the used homeplug adaptor seems not to support this feature. That's why we need to "guess" some attenuation values for the next step.
9. The charger sends ATTEN_CHAR.IND, which contains the number of sounds and for each group the attenuation in dB. Pitfall: The car may ignore
implausible values (e.g. all zero dB), and the process may be stuck.
10. The car receives the ATTEN_CHAR.IND. If it would receive multiple of them from different chargers (due to cross-coupling), the car
decides based on the attenuation levels, which of the charges is the nearest.
11. The car sends ATTEN_CHAR.RSP to the charger which reported the loudest signals.
12. The car sends SLAC_MATCH.REQ to the charger. This means, it wants to pair with it.
13. The charger responds with SLAC_MATCH.CNF. This contains the self-decided NID (network ID) and NMK (network membership key).
14. The car receives the SLAC_MATCH.CNF, takes the NID and NMK from this message, and configures its homeplug modem with this data.
15. Now, the homeplug modems of the car and of the charger have formed a "private" Homeplug network. The RF traffic can only be decoded by
participants who are using the same NID and NMK.
16. The car wants to know the chargers IP address. In computer networks, a DHCP would be a usual way to do this. In the CCS world, a different
approach is used: SDP, which is the SECC discovery protocol. The DHCP may be also supported as fallback.
17. The car sends a broadcast message "Is here a charger in this network?". Technically, it is an IPv6.UDP.V2GTP.SDP message
with 2 bytes payload, which defines the security level expected by the car. In usual case, the car says "I want unprotected TCP.".
18. The charger receives the SDP request, and sends a SDP response "My IP address is xy, and I support unprotected TCP."
19. The car wants to make sure, that the IP addresses are unique and the relation between IP address and MAC address is clear. For
this, it sends a "Neighbour solicitation". (This looks a little bit oversized, because only two participants are in the local network, and
their addresses have already been exchanged in the above steps. But ICMP is standard technology.)
20. The charger responds to the neighbor solicitation request with a neighbor advertisement. This contains the MAC address of the charger.
In the case, we use this pyPLC project as charger, we rely on the operating system that it covers the ICMP. On Win10, this works perfectly,
the only thing we must make sure, that the MAC and IPv6 of the ethernet port are correctly configured in the python script.
21. Now, the car and the charger have a clear view about addressing (MAC, IPv6).
22. The car requests to open a TCP connection to chargerIP at port 15118.
23. The charger, which was listening on port 15118, confirms the TCP channel. (Todo: not yet implemented)
24. Now, the car and the charger have a reliable, bidirectional TCP channel.
25. The car and the charger use the TCP channel, to exchange V2GTP messages, with EXI content.
26. The charger is the "server" for the EXI, it is just waiting for requests from the car. The car is the "client", it actively
initiates the EXI data exchange.
26. Todo: The car walks through different states to negotiate, start and supervise the charging process.




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

### 2022-10-21 SLAC, SDP and ICMP are working
Using the TPlink and Win10 laptop as evse, the python script runs successfully the SLAC and SDP (SECC discovery protocol). Afterwards, the car uses
neighbor solicitation (ICMP) to confirm the IPv6 address, and the Win10 responds to it. The car tries to open the TCP on port 15118, this is failing
because of missing implementation of the listener on PC side.

(further steps ongoing)
