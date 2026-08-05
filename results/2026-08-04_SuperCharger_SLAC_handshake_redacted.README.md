# Tesla Supercharger SLAC handshake capture (redacted)

`2026-08-04_SuperCharger_SLAC_handshake_redacted.pcap` — a real HomePlug AV /
SLAC (ISO 15118-3) handshake captured on the CP powerline between a Tesla
vehicle and a Tesla Supercharger, tapped with a sniffing HomePlug AV modem.
13 frames.

## What's in it

The sniffing modem only demodulated the EVSE's own transmissions (see
"Known limitation" below), so this is an **EVSE-sourced SLAC response
ladder**:

| # | frames | type |
|---|---|---|
| 1 | 1 | `CM_SLAC_PARM.CNF` (0x6065) |
| 2 | 10 | Qualcomm Atheros vendor MME, mmtype `0xa14e` — EVSE broadcast sounding tone-map indications (part of the `CM_MNBC_SOUND` phase; not decoded by name in Wireshark's public HomePlug-AV dissector, shown as "Unknown 0xa14e") |
| 3 | 1 | `CM_ATTEN_CHAR.IND` (0x606e), Groups = 58, Avg. Attenuation = 27.67 dB |
| 4 | 1 | `CM_SLAC_MATCH.CNF` (0x607d), carries the negotiated NID/NMK |

Timestamps span ~1.34s, consistent with the real SLAC attenuation-characterization
window (sounding phase + CNF/IND).

## Known limitation: EVSE-side only, no PEV REQ frames

This is a **single-tap capture** — the sniffing modem's RX only locked onto
the EVSE's transmissions. None of the matching PEV-sourced REQ frames
(`CM_SLAC_PARM.REQ` 0x6064, `CM_ATTEN_CHAR.REQ` 0x606d, `CM_SLAC_MATCH.REQ`
0x607c) are present — this is a tap-position/RX-asymmetry artifact of a
single passive modem on this run (most likely a directional RX-sensitivity
effect where the sniffing modem was coupled close to the EVSE end of the
run, or the sniffing modem itself acting as a topological endpoint rather
than a passive tap), not a filtered or edited-out omission. A two-modem
bridge (one coupled at each end) is planned for a future capture to fix
this. Useful as a reference for the EVSE-side response/indication shapes and
real-world attenuation values; not a complete bidirectional ladder.

## Redaction

Captured from a real vehicle and charger, so it's been redacted before
sharing:

- Car MAC substituted to a synthetic Tesla-OUI address (`4c:fc:aa:00:00:01`)
  everywhere it appears — both the Ethernet header and the SLAC MME body
  fields that carry it (e.g. `CM_SLAC_MATCH.CNF`'s PEV MAC field).
- EVSE MACs substituted to synthetic addresses under the same Tesla OUI
  (`98:ed:5c:00:00:02` / `98:ed:5c:00:00:03`), keeping the two EVSE
  identities (directed-response vs. broadcast-sound) distinct since that
  distinction is part of the protocol picture.
- mDNS frames (capture rig hostname) and 52 local Pi↔modem HomePlug-AV
  housekeeping MMEs (`GET_SW.REQ/CNF`, `NW_INFO`, `LINK_STATUS`, etc. between
  the capture host and its own directly-attached modem chip — not powerline
  traffic to/from the car) were dropped entirely, leaving only the SLAC
  handshake frames actually exchanged over the powerline.
- NID, NMK, attenuation values, and all other protocol fields are left
  untouched — they're ephemeral session values, not personal data, and are
  what makes the capture useful as a reference.
