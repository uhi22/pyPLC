# Test Results on different Real-World Chargers

## ABB Terra 53 Triple Charger

Test site: e.g. https://www.goingelectric.de/stromtankstellen/Deutschland/Ingolstadt/hagebaumarkt-Siemensstrasse-1/48209/

Test results of version v0.2
- [x] SLAC
- [x] SDP
- [x] TCP connection
- [x] EXI
    - [x] DIN SupportedApplicationProtocol
	- [x] DIN SessionSetup
	- [x] DIN ServiceDiscovery
	- [x] DIN ChargeParameterDiscovery
	- [ ] DIN CableCheck
	- [ ] DIN PreCharge
	- [ ] DIN PowerDelivery, CurrentDemand

## ABB Terra HPC

Test site e.g. https://www.goingelectric.de/stromtankstellen/Deutschland/Koesching/Total-Tankstelle-Ruppertswies-6/63794/

Test results tbd

## Alpitronic HPC HYC300

Test site: e.g. https://www.goingelectric.de/stromtankstellen/Deutschland/Ingolstadt/Dehner-Garten-Center-Degenhartstrasse-Degenhartstrasse-2/71112/

Test results of version v0.3
- [x] SLAC
- [x] SDP
- [x] TCP connection
- [x] EXI
    - [x] DIN SupportedApplicationProtocol
	- [x] DIN SessionSetup
	- [x] DIN ServiceDiscovery
	- [x] DIN ChargeParameterDiscovery
	- [x] DIN ContractAuthentication
	- [ ] DIN CableCheck
	- [ ] DIN PreCharge
	- [ ] DIN PowerDelivery, CurrentDemand

## Compleo Cito BM 500

Test site: e.g. https://www.goingelectric.de/stromtankstellen/Deutschland/Koesching/EDEKA-Ingolstaedter-Strasse-114/62619/

Test results of version v0.4
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
	- [x] DIN PreCharge ok, but at the end the state machine runs into timeout. Issue 15.
	- [ ] DIN PowerDelivery, CurrentDemand

## Efacec QC45 Triple Charger

Test site e.g. https://www.goingelectric.de/stromtankstellen/Deutschland/Hepberg/Koeschinger-Forst-West-A9/15982/

Test results tbd

## Efacec HPC Efapower Kiosk HV175

Test site e.g. https://www.goingelectric.de/stromtankstellen/Deutschland/Neufahrn-bei-Freising/Fuerholzen-West-A9/22771/

Test results tbd

## Ionity Tritium Veefil-PK

Test site: e.g. https://www.goingelectric.de/stromtankstellen/Deutschland/Hepberg/IONITY-Koeschinger-Forst-Ost-A9/37875/

Test results tbd

## Porsche

Test site e.g. https://www.goingelectric.de/stromtankstellen/Deutschland/Ingolstadt/Audi-Forum-Ettinger-Strasse/7970/

Test results tbd

## Tesla Supercharger V3

Test site e.g. https://www.goingelectric.de/stromtankstellen/Deutschland/Koesching/Supercharger-Car-Wash-Ruppertswies-4/69557/

Test results
- [ ] SLAC: fails. It sends SLAC_PARAM_CNF, but nothing more.

