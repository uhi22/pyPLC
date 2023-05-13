# Test Results on different Real-World Chargers

## ABB Terra 53 Triple Charger

Test site: e.g. https://www.goingelectric.de/stromtankstellen/Deutschland/Ingolstadt/hagebaumarkt-Siemensstrasse-1/48209/

Test results of version v0.4-7-g7cea8b5 (2022-12-21, Köschinger Forst Ost)
- [x] SLAC
- [x] SDP
- [x] TCP connection
- [x] EXI
    - [x] DIN SupportedApplicationProtocol
	- [x] DIN SessionSetup
	- [x] DIN ServiceDiscovery
	- [x] DIN ServicePaymentSelection
	- [x] DIN ContractAuthentication
	- [x] DIN ChargeParameterDiscovery
	- [x] DIN CableCheck
	- [x] DIN PreCharge
	- [x] DIN PowerDelivery Start
	- [x] DIN CurrentDemand: Light bulb demo works
	- [x] DIN PowerDelivery Stop
	- [ ] DIN WeldingDetection no response 2022-12-21T08:50:36.640899, issue 17
	- [ ] DIN SessionStop
- [x] Inlet voltage measurement

## ABB Terra HPC

Test site e.g. https://www.goingelectric.de/stromtankstellen/Deutschland/Koesching/Total-Tankstelle-Ruppertswies-6/63794/

Test results of version v0.4-7-g7cea8b5 (2022-12-21)
- [x] SLAC
- [x] SDP
- [x] TCP connection
- [x] EXI
    - [x] DIN SupportedApplicationProtocol
	- [x] DIN SessionSetup
	- [x] DIN ServiceDiscovery
	- [x] DIN ServicePaymentSelection
	- [x] DIN ContractAuthentication
	- [x] DIN ChargeParameterDiscovery
	- [x] DIN CableCheck
	- [x] DIN PreCharge
	- [x] DIN PowerDelivery Start
	- [x] DIN CurrentDemand: Light bulb demo works
	- [x] DIN PowerDelivery Stop
	- [ ] DIN WeldingDetection: No response 2022-12-21T08:36:29.943830, issue 17
	- [ ] DIN SessionStop
- [x] Inlet voltage measurement

## Alpitronic HPC HYC300

Test site: e.g. https://www.goingelectric.de/stromtankstellen/Deutschland/Ingolstadt/Dehner-Garten-Center-Degenhartstrasse-Degenhartstrasse-2/71112/

Test results of version v0.4-7-g7cea8b5 (2022-12-21)
- [x] SLAC
- [x] SDP
- [x] TCP connection
- [x] EXI
    - [x] DIN SupportedApplicationProtocol
	- [x] DIN SessionSetup
	- [x] DIN ServiceDiscovery
	- [x] DIN ServicePaymentSelection
	- [x] DIN ContractAuthentication
	- [x] DIN ChargeParameterDiscovery
	- [x] DIN CableCheck
	- [x] DIN PreCharge
	- [x] DIN PowerDelivery Start
	- [x] DIN CurrentDemand: Light bulb demo works
	- [x] DIN PowerDelivery Stop
	- [ ] DIN WeldingDetection: "ResponseCode": "FAILED", issue 17
	- [ ] DIN SessionStop: No response
- [x] Inlet voltage measurement (shows 500V during cable check, and 230V during precharge)

## Circontrol

First test negative, see https://openinverter.org/forum/viewtopic.php?p=56268#p56268.
The SLAC works, but after SetKey we do not see the chargers modem.

## Compleo Cito BM 500

Test site: e.g. https://www.goingelectric.de/stromtankstellen/Deutschland/Koesching/EDEKA-Ingolstaedter-Strasse-114/62619/

Test results of version v0.7 (2023-04-19)
- [x] SLAC
- [x] SDP
- [x] TCP connection
- [x] EXI
    - [x] DIN SupportedApplicationProtocol
	- [x] DIN SessionSetup
	- [x] DIN ServiceDiscovery
	- [x] DIN ServicePaymentSelection
	- [x] DIN ContractAuthentication
	- [x] DIN ChargeParameterDiscovery
	- [x] DIN CableCheck (10s loop ongoing, then finished OK)
	- [x] DIN PreCharge
	- [x] DIN PowerDelivery
      [x] DIN CurrentDemand: With no load and later light bulb connected, the charger has massive problems to regulate the voltage. It shoots over to 400V and later turns off completely, instead of regulating to the target 230V. Log: results/2023-04-19_compleo_pyPlc_lightbulb_failedBadRegulation.pcapng and 2023-04-19_compleo_pyPlc_lightbulb_failedBadRegulation.pcapng.decoded.txt

## Efacec QC45 Triple Charger

Test site e.g. https://www.goingelectric.de/stromtankstellen/Deutschland/Hepberg/Koeschinger-Forst-West-A9/15982/

Test results of version v0.4-7-g7cea8b5 (2022-12-21)
- [x] SLAC
- [x] SDP
- [x] TCP connection
- [x] EXI
    - [x] DIN SupportedApplicationProtocol
	- [x] DIN SessionSetup
	- [x] DIN ServiceDiscovery
	- [x] DIN ServicePaymentSelection
	- [ ] DIN ContractAuthentication: Due to defective charger, no authorization possible via app or RFID.

## Efacec HPC Efapower Kiosk HV175

Test site e.g. https://www.goingelectric.de/stromtankstellen/Deutschland/Neufahrn-bei-Freising/Fuerholzen-West-A9/22771/

Test tbd

## Ionity Tritium Veefil-PK

Test site: e.g. https://www.goingelectric.de/stromtankstellen/Deutschland/Hepberg/IONITY-Koeschinger-Forst-Ost-A9/37875/

Test results of version v0.4-7-g7cea8b5
- [x] SLAC
- [x] SDP
- [x] TCP connection
- [x] EXI
    - [x] DIN SupportedApplicationProtocol
	- [x] DIN SessionSetup
	- [x] DIN ServiceDiscovery
	- [x] DIN ServicePaymentSelection
	- [x] DIN ContractAuthentication
	- [x] DIN ChargeParameterDiscovery
	- [x] DIN CableCheck
	- [x] DIN PreCharge
	- [x] DIN PowerDelivery Start
	- [ ] DIN CurrentDemand: With the light-bulb configuration, the charger overshoots the intended voltage, because no load is connected at the start of the charging loop. Then, after a few seconds, the charger stops.
	- [ ] DIN PowerDelivery Stop
	- [ ] DIN WeldingDetection
	- [ ] DIN SessionStop
- [x] Inlet voltage measurement

## Kempower satellite

Tested by celeron55 with his fork https://github.com/celeron55/pyPLC 2023-05-03.

Charging works, see https://openinverter.org/forum/viewtopic.php?p=56188&sid=9579fd29268d0e332c81ed528f59f09b#p56188

## Porsche

Test site e.g. https://www.goingelectric.de/stromtankstellen/Deutschland/Ingolstadt/Audi-Forum-Ettinger-Strasse/7970/

Test results tbd

## Siemens

Charging works, see https://openinverter.org/forum/viewtopic.php?p=56478#p56478

## Tesla Supercharger V2

Charging works, see https://openinverter.org/forum/viewtopic.php?p=56478#p56478

## Tesla Supercharger V3

Test site e.g. https://www.goingelectric.de/stromtankstellen/Deutschland/Koesching/Supercharger-Car-Wash-Ruppertswies-4/69557/
or https://www.goingelectric.de/stromtankstellen/Deutschland/Pfaffenhofen-an-der-Ilm/Supercharger-Hotel-Strasshof-Siebenecken-1/44134/

Test results of version v0.5-12-g23b1384, on 2023-03-02
- [x] SLAC
- [x] SDP
- [x] TCP connection
- [x] EXI
    - [x] DIN SupportedApplicationProtocol
	- [x] DIN SessionSetup
	- [x] DIN ServiceDiscovery
	- [x] DIN ServicePaymentSelection
	- [x] DIN ContractAuthentication
	- [x] DIN ChargeParameterDiscovery
	- [ ] DIN CableCheck: The cable check runs into timeout. No real voltage on the pins. Maybe caused by wrong sessionId, see issue 18.
	- [ ] DIN PreCharge
	- [ ] DIN PowerDelivery Start
	- [ ] DIN CurrentDemand
	- [ ] DIN PowerDelivery Stop
	- [ ] DIN WeldingDetection
	- [ ] DIN SessionStop

## Tritium 75kW

Charging works, see https://openinverter.org/forum/viewtopic.php?p=56268#p56268
