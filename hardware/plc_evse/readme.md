# PLC EVSE

For use together with pyPLC.

This is a KiCad 8 project. Only the schematic, no board.

### BOM

* C1, C2, C3: elcap, 100µF, 25V
* C20: ceramic, 1nF (something between 1nF and 2.2nF is fine)
* U1: op-amp LF355
* U2, U3: isolated DCDC converter, 5V to 12V, 1W, e.g. B0512S-1WR3
* R1: 1k
* R2: 270ohm
* R5: 56k
* R6: 100k
* R7: 220k
* R8, R9: 120k (does not really matter, also 100k would be fine)
* R20: 180ohm (does not really matter. Something between 100ohm and 330ohm.)
* D1, D2: LEDs WS2812B. Also one would be sufficient.
* RV1: potentiometer e.g. 10k linear (also 1k or 22k would be fine)
* A1: Arduino Nano
* Prototyping board 100mm x 106mm
* Housing 3D printed, FreeCad mini-evse-housing.FCStd, or step: mini-evse-housing.step
* For power supply: USB A cable, cutted and soldered to the board.
