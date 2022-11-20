# CCS sniffing: Some try-outs with Python and network adaptor low-level communication

## Goal
This project tries to use cheap powerline network adaptors for communication with electric cars charging system.

There are three different use cases, where this project can be helpful:
1. Sniffing the traffic between an CCS charger and a car. For instance to measure which side is the limiting element for reduced charging power.
In this project, we call this mode *ListenMode*.
2. Building a charger for CCS or for AC with digital communication. We call this *EvseMode*.
3. Building a charging unit for a car which does not support powerline communication. Let's call it *PevMode*.

## References
* [i] https://www.goingelectric.de/wiki/CCS-Technische-Details/
* [ii] https://openinverter.org/forum/viewtopic.php?p=37085#p37085
* [iii] https://github.com/qca/open-plc-utils
* [iv] https://github.com/karpierz/pcap-ct
* [v] https://github.com/FlUxIuS/V2Gdecoder
* [vi] https://github.com/SwitchEV/iso15118
* [vii] https://books.google.de/books?id=WYlmEAAAQBAJ&pg=PA99&lpg=PA99&dq=%22ampsnif%22&source=bl&ots=hqCjdFooZ-&sig=ACfU3U0EleLZQu0zWhHQZGktp8OytCMrLg&hl=de&sa=X&ved=2ahUKEwjT0Yq88P36AhWj_rsIHeGMA5MQ6AF6BAgKEAM#v=onepage&q=%22ampsnif%22&f=false How to enable sniffer mode.
* [viii] https://www.mdpi.com/2076-3417/6/6/165/htm "Building an Interoperability Test System for Electric Vehicle Chargers Based on ISO/IEC 15118 and IEC 61850 Standards", including V2G message sequence chart
* [iix] https://www.oppcharge.org/dok/ISO_15118-2_OpportunityCharging_Rev1.3.0.pdf Pantograph specific differences with some insight into ISO15118.

## Quick start / overview
- Modify a PLC adaptor hardware, that it runs on battery
- Modify the configuration of the PLC adaptor, that it supports HomePlug Green Phy including the SLAC.
- Install wireshark to view the network traffic
- Install Pcap-ct python library
- Patch Pcap-ct to support non-blocking operation
- Get and compile the exi decoder/encoder from http://github.com/uhi22/OpenV2Gx
- Run `python pyPlc.py` and use keyboard to trigger actions, or
- Run `python pyPlc.py E` for EVSE (charger) mode, or
- Run `python pyPlc.py P` for PEV mode, or
- Run `python pyPlc.py L` for Listen mode

## Architecture
![architectural overview](doc/pyPlc_architecture.png)

## Hardware preparation
See [Hardware manual](doc/hardware.md)

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
Pitfall: Pcap-ct does not work with Python 3.4. After update to Python 3.8, it works.

See See [Raspberry installation manual](doc/installation_on_raspberry.md)

## Example flow
This chapter describes the start of a charging session, considering all layers. It is NOT the description of the currently
implemented features, it is just a reference for understanding and further development.

Precondition: On charger side, there is a homeplugGP-capable device present, which is configured as CentralCoordinator.
1. The charger (Supply entity communication controller, SECC) creates a "random" value for NID (network ID) and
NMK (network membership key), and configures its homeplug modem with these values.
2. The charger provides 12V on the control pilot (CP) line (State A).
3. The user connects the plug into the car.
4. The car pulls the 12V at CP line to 9V (State B).
5. The charger sees the level change on CP and applies 5% PWM on CP.
6. The car sees the 5%, and interprets it as request for digital communication. It wakes up its communication controller (electric vehicle
communication controller, EVCC) and homeplug modem.
7. The car sees homeplug coordinator packets on the CP, and starts the SLAC sequence by sending SLAC_PARAM.REQ. Can be also two times.
8. The charger receives the SLAC_PARAM.REQ and confirms it with SLAC_PARAM.CNF.
9. The car sends START_ATTEN_CHAR.IND, to start the attenuation measurement. In total 3 times.
10. The car sends MNBC_SOUND.IND, to provide different sounds (signals different frequency ranges). In total 10 times.
11. The homeplug modem in the charger should measure the signal strength, and report the values to the SECC in an ethernet frame ATTEN_PROFILE.IND.
However, the used homeplug adaptor with AR7420 seems not to support this feature. That's why we need to "guess" some attenuation values
for the next step.
12. The charger sends ATTEN_CHAR.IND, which contains the number of sounds and for each group the attenuation in dB. Pitfall: The car may ignore
implausible values (e.g. all zero dB), and the process may be stuck.
13. The car receives the ATTEN_CHAR.IND. If it would receive multiple of them from different chargers (due to cross-coupling), the car
decides based on the attenuation levels, which of the charges is the nearest.
14. The car sends ATTEN_CHAR.RSP to the charger which reported the loudest signals.
15. The car sends SLAC_MATCH.REQ to the charger. This means, it wants to pair with it.
16. The charger responds with SLAC_MATCH.CNF. This contains the self-decided NID (network ID) and NMK (network membership key).
17. The car receives the SLAC_MATCH.CNF, takes the NID and NMK from this message, and configures its homeplug modem with this data.
18. Now, the homeplug modems of the car and of the charger have formed a "private" Homeplug network (AV local network, AVLN). The RF
traffic can only be decoded by participants who are using the same NID and NMK.
19. The car wants to know the chargers IP address. In computer networks, a DHCP would be a usual way to do this. In the CCS world, a different
approach is used: SDP, which is the SECC discovery protocol. The DHCP may be also supported as fallback.
20. The car sends a broadcast message "Is here a charger in this network?". Technically, it is an IPv6.UDP.V2GTP.SDP message
with 2 bytes payload, which defines the security level expected by the car. In usual case, the car says "I want unprotected TCP.".
21. The charger receives the SDP request, and sends a SDP response "My IP address is xy, and I support unprotected TCP."
22. The car wants to make sure, that the IP addresses are unique and the relation between IP address and MAC address is clear. For
this, it sends a "Neighbour solicitation". (This looks a little bit oversized, because only two participants are in the local network, and
their addresses have already been exchanged in the above steps. But ICMP is standard technology.)
23. The charger responds to the neighbor solicitation request with a neighbor advertisement. This contains the MAC address of the charger.
In the case, we use this pyPLC project as charger (*EvseMode*), we rely on the operating system that it covers the ICMP. On Win10,
this works perfectly, the only thing we must make sure, that the MAC and IPv6 of the ethernet port are correctly configured in the
python script. Use `ipconfig -all` on Windows, to find out the addresses.
24. Now, the car and the charger have a clear view about addressing (MAC adresses, IPv6 addresses).
25. The car requests to open a TCP connection to charger at port 15118.
26. The charger, which was listening on port 15118, confirms the TCP channel.
27. Now, the car and the charger have a reliable, bidirectional TCP channel.
28. The car and the charger use the TCP channel, to exchange V2GTP messages, with EXI content.
29. The charger is the "server" for the EXI, it is just waiting for requests from the car. The car is the "client", it actively
initiates the EXI data exchange.
30. The car walks through different states to negotiate, start and supervise the charging process. From communication point of view,
the complete process uses XML data, which is packed in EXI frames, which in turn are transported in the TCP channel mentioned above. The overview over
the various steps is visible in a sequence chart in [viii].
31. The first request-response-pair decides about which XML schema is used for the later communication. This first communication uses
a special XML schema, the "application handshake" schema. Afterwards, one of the following three schemas will be used: DIN, ISO1, ISO2. These
are different flavours of the DIN/ISO15118 specification, which have small but significant differences. This means, the negotiation of
the exact schema is essential for the next step.
31. The car announces the supported application protocols, e.g. DIN or ISO, using the SupportedApplicationProtocolRequest.
32. The charger chooses the best application protocol from the list, and announces the decision with SupportedApplicationProtocolResponse.
33. The car initiates the charging session with SessionSetupRequest. The SessionID in
this first message is zero, which is the reserved number meaning "new session".
34. The charger confirms the session with SessionSetupResponse. In this message, the charger sends for the first time
a new, non-zero SessionID. This SessionID is used in all the upcoming messages from both sides.
35. The car sends ServiceDiscoveryRequest. Usually, this means it says "I want to charge" by setting serviceCathegory=EVCharging.
36. The charger confirms with ServiceDiscoveryResponse. This contains the offered services and payment options. Usually it says which type
of charging the charger supports (e.g. AC 1phase, AC 3phase, or DC according CCS https://en.wikipedia.org/wiki/IEC_62196#FF), and that
the payment should be handled externally by the user, or by the car.
37. The car sends PaymentServiceSelectionRequest. Usually (in non-plug-and-charge case), the car says "I cannot pay, something else should
handle the payment", by setting paymentOption=ExternalPayment. Optionally it could announce other services than charging, e.g. internet access.
38. The charger confirms with PaymentServiceSelectionResponse.
39. The car sends AuthorizationRequest. In non-plug-and-charge case this is most likely not containing relevant data.
40. The charger confirms with AuthorizationResponse.
41. The car sends ChargeParameterRequest. This contains the wanted RequestedEnergyTransferMode, e.g. to select
DC or AC and which power pins are used. The car announces the maximum current limit and the maximum voltage limit.
42. The charger confirms with ChargeParameterResponse. The contains the limits from charger side, e.g. min and max voltage,
min and max current. Now, the initialization phase of the charging session is finished.
43. The car changes to CP State to C or D, by applying an additional resistor between CP and ground.
44. The car sends CableCheckRequest. This contains the information, whether the connector is locked.
45. The charger applies voltage to the cable and measures the isolation resistance.
46. The charger confirms with CableCheckResponse.
47. The car sends PreChargeRequest. With this, the car announces the target voltage of the charger before closing the circut. The goal
is, to adjust the chargers output voltage to match the cars battery voltage. Also a current limit (max 2A) is sent.
48. The charger confirms with PreChargeResponse. This response contains the actual voltage on the charger.
49. The charger adjusts its output voltage according to the requested voltage.
50. The car measures the voltage on the inlet and on the battery.
51. The above steps (PreChargeRequest, PreChargeResponse, measuring physical voltage) are repeating, while the
physical voltage did not yet reach the target voltage.
51. If the difference is small enough (less than 20V?), the car
closes the power relay.
51. The car sends PowerDelivery(Start)Request.
52. The charger confirms with PowerDeliveryResponse.
53. The car sends CurrentDemandRequest (repeated while the charging is ongoing). In this message, the car tells the charger the target voltage and
target current.
54. The charger confirms with CurrentDemandResponse. This contains the measured voltage, measured current, and flags which show which limitation
is active (current limitation, voltage limitation, power limitation).
55. The car sends PowerDelivery(Stop)Request.
56. The charger confirms with PowerDeliveryResponse.
57. The car sends WeldingDetectionRequest.
58. The charger confirms with WeldingDetectionResponse.
59. The car sends SessionStopRequest.
60. The charger confirms with SessionStopResponse.



## Change history / functional status
### 2022-10-19 [*EvseMode*] Communication/AVLN with Ioniq car established
* Using a TPlink TL-PA4010P with firmware MAC-QCA7420-1.4.0.20-00-20171027-CS and the PIB configuration file patched for evse according to the open-plc-utils docu.
* Python software running on Win10, Python 3.10.8
* On control pilot, sending 5% PWM to initiate digital communication with the car
* Since the TPlink is configured as coordinator, it sends "alive" messages, and the IONIQ starts sending the SLAC_PARAM.REQ.
* Per keystroke, we trigger a SET_KEY before the car is connected. The TPlink responds with "rejected", but this is normal, the LEDs are turning off and on, key is accepted.
* Python script interprets the relevant incoming messages (SLAC_PARAM.REQ, MNBC_SOUND.IND, SLAC_MATCH.REQ) and reacts accordingly.
* After successfull SLAC sequence, all three LEDs on the TPlink are ON, means: Network (AVLN) is established.
* In wireshark, we see that the car is sending UDP multicast messages to destination port 15118. This looks like a good sign, that it wants a ISO15118 compatible communication.
![image](https://user-images.githubusercontent.com/98478946/196766285-1c3152f7-31db-4b5f-98b1-9f1216f9b9de.png)

### 2022-10-19 [*ListenMode*] Sniffing mode not yet working with the TPlink adaptors
* with a Devolo dLAN 200 AVplus, software INT6000-MAC-4-4-4405-00-4497-20101201-FINAL-B in original parametrization, it is possible
to see the complete SLAC traffic (both directions) which sniffing the communication between a real charger and a real car. This does
NOT work with the TPlink adaptors. They route only "their own" direction of the traffic to the ethernet. Means: The pev-configured device
does not see the real car, and the evse-configured device does not see the real charger. This is bad for sniffing.

### 2022-10-21 [*EvseMode*] SLAC, SDP and ICMP are working
Using the TPlink and Win10 laptop as evse, the python script runs successfully the SLAC and SDP (SECC discovery protocol). Afterwards, the car uses
neighbor solicitation (ICMP) to confirm the IPv6 address, and the Win10 responds to it. The car tries to open the TCP on port 15118, this is failing
because of missing implementation of the listener on PC side.

### 2022-10-26 [*ListenMode*] Network/AVLN is established
Using the TPlink in EVSE mode and Win10 laptop, listening to a communication setup between real car and real alpitronics charger, the python script
successfully extracts the NID and NMK from the SLAC_MATCH response, sets this information into the TPlink, and the TPlink turns three
LEDs on. Means: Network established. When we send a broadcast software version request, we get three responses: One from the TPlink, one from the
PLC modem of the car, and one from the PLC modem of the charger. This confirms, that the network is established.
But: From the higher level communication (IPv6, UDP, TCP) we see only the broadcast neighbor solicitation at the beginning. The remaining traffic
is hidden, most likely because the TPlink "too intelligent", it knows who has which MAC address and hides traffic which is not intended for the
third participant in the network. Trace in results/2022-10-26_WP4_networkEstablishedButHiddenCommunication.pcapng

### 2022-11-09 [*EvseMode*][*PevMode*] Exi decoder first steps working
Using EXI decoder/encoder from basis https://github.com/Martin-P/OpenV2G and created fork https://github.com/uhi22/OpenV2Gx to
provide a command-line interface, which can be used by the python script. The OpenV2G includes generated source code for four
xml schemas (Handshake, DIN, ISO1, ISO2), provided by Siemens. Seems to be good maintained and is very efficient, because the
decoder/encoder are directly available as C code, dedicated for each schema. This skips the slow process of reading the schema,
parsing it, creating the grammer information. On Windows10 notebook, measured 15ms for decoder run from python via command line.
The OpenV2G was compiled on Windows10 using the included makefile, using the `mingw32-make all`.
The OpenV2G decoder/encoder code reveals some differences between the different schemas (DIN versus ISO). As starting point, only the
DIN schema is considered in the command line interface and python part.

The python part now contains the charging state machines for car and charger, as draft.

Using the TPlink and Win10 laptop as evse, connected to Ioniq car, the python script successfully succeeds to SLAC, TCP connection,
schema handshake, SessionSetup, ServiceDiscovery, ServicePaymentSelection. It stops on ChargeParameterDiscovery, most likely to
missing or wrong implementation. Results (log file and pcap) are stored in
https://github.com/uhi22/pyPLC/tree/master/results.

As summary, the concept with the python script together with the compiled EXI decoder works. Further efforts can be spent on
completing the missing details of the V2G messages.

### 2022-11-11 [*EvseMode*] Ioniq in the PreCharge loop
The EVSE state machine, together with the EXI decoder/encoder, is able to talk to the Ioniq car until the PreCharge loop. The
car terminates the loop after some seconds, because the intended voltage is not reached (no physical electricity connected to the
charge port). Maybe it is possible to convince the car to close the relay, just by pretending "voltage is reached" in the
PreCharge response. But maybe the car makes a plausibilization with the physical voltage, then further development would require
a physical power supply.

### 2022-11-15 [*PevMode*] Draft of SLAC sequencer
In PevMode, the software runs through the SLAC sequence with a simulated Evse. After SLAC is finished, we send a software
version request broadcast message, to find out, whether we have at least two homeplug modems in the network (one for the
car and one for the charger). If this is fulfilled, we should use the SDP to discover the chargers IPv6 address. But this
is not yet implemented.


## Biggest Challenges
- [*ListenMode*] Find a way to enable the sniffer mode or monitor mode in the AR7420. Seems to be not included in the public qca/open-plc-utils.
Without this mode, we see only the broadcast messages, not the TCP / UDP traffic between the EVSE and the PEV.
The \open-plc-utils\pib\piboffset.xml mentions a setting "SnifferEnable" at 0102 and "SnifferReturnMACAddress" starting at 0103. But setting
the enable to 1 and adding a senseful MAC address does not lead to a difference.
The docu of qca/open-plc-utils mentions ampsnif and plcsnif, but these are not included. An old
release (https://github.com/qca/open-plc-utils/archive/refs/tags/OSR-6010.zip) is mentioning VS_SNIFFER message, ampsnif, plcsnif and even
functions Monitor() and Sniffer(), but these are included from a path ../nda/ which is not part of the public repository.

Any idea how to enable full-transparency of the AR7420?

- [all modes] replace the fix-configured addresses (MAC, IP) in the python script by the real one from the operating system

## Other open topics
- [*EvseMode*] [*PevMode*] Fill V2G messages as far as needed, to convince the car to accept it.
- [*PevMode*] Implement SDP to get the chargers IPv6 address
- [*PevMode*] Testing on real charger
- improve docu (update layer diagram, improve hardware docu, add link to evse which provides the 5% PWM)
- Resolve the todo-markers in the code
- (and much more)

## FAQ

### Q1: What is the minimal setup, to catch the MAC addresses in the communication between a real charger and a real car?
- Hardware: A TPlink TL-PA4010P homeplug adaptor, with the configuration for PEV. Modified according to the hardware manual https://github.com/uhi22/pyPLC/blob/master/doc/hardware.md
- Software: Wireshark. Only wireshark. (The pyPlc project and the exi decoder is NOT necessary to sniff the MAC addresses.)

### Q2: Is it possible to use this software, to make the car closing the relay, so that I'm able to draw energy out of the car?
Good question. This depends on how strict the car is. This first hurdle is to convince the car, to close the relay. This is
done after a successful PreCharge phase. And it depends on the implementation of the car, whether it needs physically correct
voltage on the inlet before closing the relay, or whether it relies on the pretended voltage in the PreChargeResponse message.
The second hurdle is, that the car may make a plausibilization between the expected current flow (charging) and the actually
measured current flow (discharging). The car may stop the complete process, if the deviation is too high or/and too long.

However, the software will help to explore and understand the behavior of the car.

### Q3: Is it possible to use this software in a car without CCS, to make it ready for CCS charging?
That's is definitely a goal, at it looks reachable. Of course, two aspects need to be considered:
- This project is not a final product. Further development will be necessary to ensure compatibility with chargers, and make is flexible for practical use.
- Some parts are not covered by this project at all, e.g. communication with the BMS, connector lock, safety considerations.
