# Open issues

(This document will not be updated. Issues are tracked in github issues, https://github.com/uhi22/pyPLC/issues )

# Closed issues

## Issue17: Welding detection fails
- WeldingDetectionRes says "failed" on alpitronics, and no response on ABBHPC and ABBTriple
- version v0.4-7-g7cea8b5 (2022-12-21)

## Issue21: Missing fields in ChargeParameterDiscoveryReq
- In the ChargeParameterDiscoveryReq, some fields are not filled. This leads to abort on certain charger types.
- Discussion in https://openinverter.org/forum/viewtopic.php?p=54696#p54696
- Improvement in https://github.com/uhi22/OpenV2Gx/commit/4b5df391d56e15b45652605fa7ad8a7712e2acaf
- No issue on Compleo, Alpi, ABB.

## Issue18: On SuperCharger we ignore the session ID
- In the SessionSetupResponse, the SuperCharger V3 correctly provides a sessionID, e.g. "06ef0071".
- But we ignore this, and send in all next messages (starting with ServiceDiscoveryReq) the sessionID "deadbeefdeadbeef".
- The SuperCharger correctly complains with "ResponseCode": "FAILED_UnknownSession".
- logs 2023-03-02_SuperCharger_CableCheck_error.pcapng and 2023-03-02_SuperCharger_CableCheck_error.decoded.txt
- observed with Software version v0.5-12-g23b1384, on 2023-03-02.
- root cause: In main_commandlineinterface.c we check, whether the session ID has 16 characters, to represent 8 hex bytes.
But the SuperCharger provides 8 characters, to represent 4 bytes. That's why the function useSessionIdFromCommandLine()
operates with the default session ID "deadbeefdeadbeef".
- solution: in function useSessionIdFromCommandLine(), also accept shorter session IDs. And in function init_dinMessageHeaderWithSessionID(),
use a dynamic length instead of the fixed length LEN_OF_SESSION_ID (=8).
- implementation done with https://github.com/uhi22/OpenV2Gx/commit/9c08c19ce14446a316ed4059d6d5b5e07721fd9d

## [Solved] Issue20: Missing EVCCID in the SessionSetupReq
- In the SessionSetupReq, the charger expects the EVCCID filled with the cars MAC. This is missing, and leads to abort on certain charger types.
- Discussion in https://openinverter.org/forum/viewtopic.php?p=54667#p54667
- Fixed with https://github.com/uhi22/OpenV2Gx/commit/fc46c3ca802f08c57120a308f69fb4d1ce14f6b6 and https://github.com/uhi22/pyPLC/commit/9b39bff85a04071e5d92d613197422033f0c1d8d

## Issue19: Wrong determination of MAC and IPv6
- SOLVED in v0.7 (2023-04-19)
- On linux, the deprecated ifconfig is not a good choice. And, if multiple interfaces are present, the wrong address is fetched.
- Solution: Three parts
1. Use "ip addr" instead of "ifconfig" -> done
2. Filter for the correct interface -> done
3. Make the interface name configurable -> done

## Issue15: After end of PreCharging, the log says "re-initializing fsmPev"
- SOLVED
- observed with v0.4 on the Compleo charger
- PreCharge target voltage is reached. The fsmPev sends a message
01fe800100000012809a022189cbf75b9625a9513022800a0800
and after one second the state machine seems to run into timeout.
- same timeout issue observed on Compleo by johu with version 0.6+
- with v0.7 (2023-04-19) tested ok, see results/2023-04-19_compleo_pyPlc_lightbulb_failedBadRegulation.pcapng

## [Solved] Issue16: First CurrentDemandReq is rejected with FAILED_SequenceError and EVSE_Shutdown
- observed on Alpitronics HPC with version v0.4-6-g257e5af
- log 2022-12-20_alpi_currentDemandSequenceErrorShutdown.pcapng
- same result in two trys
- root cause: In the exi encoder, the PowerDeliveryReq.ReadyToChargeState was treated as enum as in the ISO, but in fact it must be boolean.
- Fixed with https://github.com/uhi22/OpenV2Gx/commit/a00f1fba878085629a8325281b0a29c9ce6dd72c
- Test pass 2022-12-21 with v0.4-7-g7cea8b5 on alpi, ABB HPC and ABB triple charger.

## [Solved] Issue14: Connection loss after authorization
- with version v0.4.
- same version works fine on Compleo
- could be also caused by weak power of the powerbank. The TpLink and Dieter made restart from time to time.
- to be retested with better supply and on other chargers.
- Test pass with v0.4-6-g257e5af, with the Intenso two-cell powerbank.

## [Solved] Issue12: Alpi reports "sequence error" for CableCheck
- with version v0.3.
- maybe he expects the state C, or something is wrong with the sequence before.
- Test pass with v0.4-6-g257e5af

## [Solved] Issue13: Compleo SLAC stops after SlacParamResponse
- Root cause: The Compleo ignores the StartAttenChar, if the timeout field is set to 1000ms instead of the nominal 600ms.
- Solution: implemented the nominal 600ms.
- fixed with commit cf9160c1bcb9c0760b7f67bb8a36f03c9fe9c9a1
- Test pass on Compleo with v0.4

## [Solved] Issue10: Alpi says SequenceError in ChargeParameterDiscoveryRes
- ServicePaymentSelectionRes says "ResponseCode": "OK", and has no more fields.
- Afterwards we send ChargeParameterDiscoveryReq and get ChargeParameterDiscoveryRes containing "ResponseCode": "FAILED_SequenceError".
- Analysis: In the ISO case, the ChargeParameterDiscoveryReq comes after the AuthorizationRes with EVSEProcessing=Finished. But we are using DIN, and here there is no AuthorizationRes, but ContractAuthentication instead. But, this does not
have a field EVSEProcessing. And in DIN, we have dinContractAuthenticationResType, which contains ResponseCode and EVSEProcessing (see OpenV2G, dinEXIDatatypes.h).
- Solution: Send ContractAuthenticationReq after ServicePaymentSelectionRes, and repeat it until it says "finished". Test pass with v0.3.

## [Solved] Issue11: TCP connection fails on Alpi
- Observation: On Alpitronics, the SDP works, but the TCP connect fails. The connection is rejected by the charger.
- Root cause: We used fixed port 15118 for the TCP. This is not intended, even it works on other chargers (ABB).
- Solution: use the TCP port, which was announced in the SDP response.
- Test pass with version v0.2-9-ga9b6e82.
