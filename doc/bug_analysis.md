# Open issues

## Issue12: Alpi reports "sequence error" for CableCheck
- with version v0.3.
- maybe he expects the state C, or something is wrong with the sequence before.

# Closed issues

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
