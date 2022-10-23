# Hardware for CCS Sniffing

## Homeplug adaptors

### Devolo dLAN 200 AVplus
Todo: add picture how to connect the DC power and the RF

Pro:
* Routes the SLAC traffic from RF port to Ethernet, using the original software (INT6000-MAC-4-4-4405-00-4497-20101201-FINAL-B)
and unchanged parametrization.
* Works as CentralCoordinator. This means, it sends out "coordinator packets" which enables the connected car to send out the first SLAC message.

Contra:
* Does not support the read-out of the configuration using the github.com/qca/open-plc-utils.
* Seems not to be able to send SLAC messages on the RF port.

### Devolo dLAN 1200+
Todo: add picture how to connect the DC power and the RF


### TPlink TL-PA4010P
This adaptor was suggested by https://openinverter.org/forum/viewtopic.php?p=37085#p37085 and there,
successfully used to establish a communication to the CCS charger.

Todo: add picture how to connect the DC power and the RF

Pro:
* Can be configured as pev and as EVSE, using two different configuration files (created and patches with github.com/qca/open-plc-utils)
* Is able to transmit and receive the SLAC messages, if the special config files are used.

Contra:
* In original parametrization, does not support SLAC (not routed from RF to Ethernet, and not vice versa).
* Depending on the configuration, only one direction of the SLAC is routed from RF to Ethernet. Means: Not suitable for sniffing the complete
SLAC sequence.

Power supply: Originally, it has 12V internal supply. There is a DC/DC step down converter included, which supplies the chipset with 3.3V.
Works on the original 12V supply line also with 13V/110mA, 10V/120mA, 6V/190mA, and, which reduced RF output power, down to 5V/220mA and even 4V/240mA.
Just supplying 5V from an USB power bank at the original 12V line works fine. The only drawback is a slightly reduced transmit power, because
the RF transmitter is connected to the 12V, but is is no issue, because it has anyway much too much transmit power for the CCS use case.

How to modify: Tested device: TPlink TL-PA1040P Ver 5.0
- remove the housing
- remove the AC power connector parts
- connect cables to supply the device by battery. Works with 12V, also works with 5V from an USB power bank.
- connect cables and circuit (1nF and 150ohms in series) for connecting to the pilot line.

