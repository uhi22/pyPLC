# PLC signal amplitudes

To have comparable results, we measure the peak-to-peak voltage of the preamble of the homeplug packet.

1. Homeplug modem with AR7420, supplied by 5V
10Vpp at the transformer

2. Homeplug modem with AR7420, supplied by 5V, with 150ohm series resistor between transformer and CP.
Foccci v3 (including transformer with RIK10, 2x5 turns) connected via 1m twisted pair.
3Vpp at the CP line

3. Like 2, but in the homeplug modem two additional series resistors 680ohms in the transmit path, between
the power amplifier and the transformer.

- EVSE packet: 250mVpp at the CP line 
- Foccci packet: 500mVpp at the CP line

4. Like 3, but in the homeplug modem the two 680ohm in serial and a 10ohm in parallel to the transformer.

- Foccci packet: 500mVpp at the CP line (no change, normal)
- EVSE packet: hardly measurable, in the 20mVpp range.
- Communication still works perfect.

5. Compleo 20kW triple charger

Sends very loud packets, even if no vehicle is connected.
17Vpp

6. ISO 15118-3

On both, EVSE side and EV side of the charging cable, the typical voltage is
1.3Vpp.
This is specified as "power spectral density" of typical -75dBm/Hz at 1.8MHz to 30MHz, receiver band width 9kHz with 50 ohms.

Example states the following levels:
- Transceiver output: -72dBm/Hz
- CP on EVSE: -76dBm/Hz
- CP on PEV: -78dBm/Hz
- Transceiver modem input: -81dBm/Hz
This would be 9dB between transmitter output and receiver input.

