# ISO15118 / HomePlug-AV sniffer firmware **v159** for the TP-Link TL-PA4010P V2 (QCA AR7420)

`patch_ar7420_sniffer_v159.py` turns the **official TP-Link TL-PA4010P V2 firmware (1.1.0.844)** into a
transparent sniffer for CCS charging. It overhears the SLAC handshake between a car and a charging station,
joins the HomePlug-AV network those two set up, and forwards all SLAC, SDP and V2G traffic to its Ethernet
host — so pyPLC (or Wireshark) on the host PC sees the full charging session. (It does not join ordinary
home powerline networks; it keys itself only to the car↔charger network it learns from the SLAC.)

The script is pure Python standard library, runs offline, and **contains no TP-Link or Qualcomm firmware** —
only the bytes this project changed. You supply the stock firmware yourself from a lawful copy.

> **v159 supersedes v142.** If you ran the earlier v142 build, v159 is a drop-in replacement with the same
> transparent behaviour out of the box (no configuration needed) plus the fixes in *What's new* below. v142 is
> still in this folder for reference, but new field tests should use v159.

> **⚠️ Draft release for field testing.** v159 is verified on the bench (SLAC / SDP / V2G reach the host, the
> car-TEI lookup works against a second sniffer, the EVSE session is never disturbed), but it has **not** yet
> been proven against a wide range of real chargers — which is exactly what this release is for. **Feedback and
> test results are very welcome:** open a GitHub issue on this repository, or post in the
> [openinverter forum](https://openinverter.org/forum/). Please include your hardware revision, the firmware
> tag (`261018-V159-0844`), the charger model, and how reliably the session was captured.

## ⚠️ Read this first

- **Flashing can brick the modem.** Recovery may require SPI flash access (opening the case, soldering). You
  are solely responsible; there is no warranty.
- This is a **sniffer**: from the SLAC handshake it overhears, it adopts the key of the car↔charger network
  and captures **other parties'** SLAC/SDP/V2G traffic. Use it only on sessions and vehicles you are
  **authorised** to monitor.
- Supported hardware: tested on **TL-PA4010P V2.0 and V2.4** (AR7420) running stock firmware `1.1.0.844`.
  Revision **V2.3 is most likely supported too** (same `1.1.0.844` firmware) but is untested.
- The patch script accepts the input only if its SHA-256 matches the stock `1.1.0.844` `.nvm`, so firmware from
  any other version is **refused, not mis-flashed**. It is pure Python 3, verified byte-identical on Windows 10
  and Raspberry Pi OS (WSL still to be measured).

## What's new in v159 (vs the earlier v142 build)

v159 keeps everything v142 did and adds:

- **Correct car-TEI determination.** v142 computed the car's TEI with the rule `6 − CCo − own`, which only
  holds when the network's three stations have TEIs exactly {1, 2, 3}. Chargers that hand out other TEIs (e.g. a
  Tesla Supercharger assigning TEI 10) left v142 unable to route the unicast session. v159 instead **looks the
  car's TEI up in the modem's own station table** at the SDP request, so it works regardless of the assigned
  TEIs.
- **Crash-proof against stray management messages.** On v142 a few host-side MMEs (e.g. `CM_GET_KEY`) could hit
  firmware handler space the patch had recycled and restart the modem. v159 rejects those safely and counts
  them in the status block.
- **Does not disturb the live charging session.** The per-frame TEI switching is now hidden from the modem's
  own transmit/acknowledge path, so the sniffer stays passive to the car↔charger session.
- **Four operating modes** (see *Diagnostics* below): passive, ping-pong (the default transparent sniffer),
  self-is-car and self-is-charger.
- **A readable status block** over the diagnostic MME: join/learn timing, TEIs, frame and SDP counters.

For a field test you do not need any of the diagnostics — flash it, capture, and you get the full session.

## 1. Get the stock firmware (you download it)

TP-Link package: <https://static.tp-link.com/resources/software/TL-PA4010PKIT_V2_130807.zip>
```text
zip  TL-PA4010PKIT_V2_130807.zip         SHA-256 191fccea7644cf0b9831d28c69bd9da63745ffc052a06dfb4dcb79fbc10df781
file MAC-7420-v1.1.0-01-X-FINAL.nvm      SHA-256 398f29834eaa51b0bac2ba660c74da83b6274f1ffef1400ace1c59b00f7f8d27
```
Unzip and locate `MAC-7420-v1.1.0-01-X-FINAL.nvm`.

## 2. Build the patched firmware

```sh
python patch_ar7420_sniffer_v159.py MAC-7420-v1.1.0-01-X-FINAL.nvm -o ar7420_sniffer_v159.nvm
```
The script verifies the input SHA-256, applies the patch, and verifies the output SHA-256:
```text
output ar7420_sniffer_v159.nvm           SHA-256 af67828a2b223a8da0dc6561399f8a827280c5b8e0a9940a7ba605cfc64c476b
```
If either hash does not match it stops and writes nothing.

## 3. Flash it over Ethernet (with YOUR OWN modem config)

Needs [open-plc-utils](https://github.com/qca/open-plc-utils) (`plctool`). **No PIB is shipped** — you supply
your modem's PIB so its MAC/keys are preserved:
```sh
# 1. back up your current PIB
plctool -i <iface> -p my_backup.pib <modem-mac>
# 2. write firmware + PIB, then reset
plctool -i <iface> -P my_backup.pib -N ar7420_sniffer_v159.nvm -R <modem-mac>
```
After the reset the modem runs the sniffer build. Point pyPLC / Wireshark at the host interface.

**Capture on a promiscuous-capable interface.** The sniffer forwards the *whole* session — the SLAC
handshake plus the unicast SDP response and V2G TCP (port 61851) data plane. Those unicast frames are
addressed to the car's and charger's MACs, not the host's, so a NIC that silently filters by destination
MAC (many built-in laptop ports do) will show the broadcast/multicast SLAC but drop the unicast — making
it look like unicast forwarding is broken when it is not. Capture with a promiscuous-capable adapter (a
USB Ethernet dongle is reliable), and make sure your capture tool enables promiscuous mode: `tcpdump` and
Wireshark do by default; a raw socket in your own script does **not** unless you set it. If you see SLAC
but no SDP/V2G, suspect the capture interface first.

**PIB configuration (required):** this build **requires** a PIB set up in the **PEV role** — the same modem
configuration pyPLC uses for its adapters. If your modem's PIB is not already a PEV PIB, set one up with pyPLC's
[step-by-step PIB setup](https://github.com/uhi22/pyPLC#step-by-step) and flash the sniffer firmware together
with *that* PIB in the command above.

## 4. Verify the flash

The patch deliberately **keeps the stock version string**, so `plctool -r` still reports `1.1.0.844` and cannot
tell the sniffer from stock firmware. Confirm the sniffer build with the included reader (Linux, root):
```sh
sudo python3 identify_ar7420_firmware.py <iface> <modem-mac>
# -> sniffer build tag: 261018-V159-0844
```
Seeing the tag means the sniffer firmware is running; `no sniffer tag` means the modem is still stock
(or unreachable / wrong interface). The same reader works for any build in this series; the tag tells you which.

## 5. Roll back

Re-flash the stock firmware the same way:
```sh
plctool -i <iface> -P my_backup.pib -N MAC-7420-v1.1.0-01-X-FINAL.nvm -R <modem-mac>
```

## 6. Diagnostics (optional — not needed for a capture)

v159 exposes a diagnostic side-channel over the vendor `VS_SW_VER` (GET_SW) MME. A normal GET_SW request is
answered byte-for-byte as stock; a request carrying one of the magic markers below selects a sub-mode. All of
this is **optional** — the default build captures the full session with no interaction.

> The pyPLC project's companion reader scripts (`rpi/herbst/status_block.py`, `rpi/herbst/pp_status.py`) decode
> the blocks below. The raw request/response format is described in
> [`patch_explanation_v159.md`](patch_explanation_v159.md) §6.

### 6.1 Operating modes

The build boots in **mode 1 (ping-pong)** — the transparent sniffer. The mode is the `armed`/`mode` byte of the
ping-pong control block at RAM address `0x22c4f8`; set it with the `WRM1` sub-mode (width 1):

| Mode | Name | Behaviour |
|---|---|---|
| 0 | passive | OWN_TEI held at the sniffer's own real TEI; learning continues, no session routing |
| **1** | **ping-pong** (default) | flips OWN_TEI per frame between charger and car — **full transparent capture** |
| 2 | selfIsCar | once learned, holds OWN_TEI = the car's TEI (impersonate the car side) |
| 3 | selfIsCharger | once learned, holds OWN_TEI = the charger's TEI |
| >3 | treated as passive | |

For a plain capture, leave it in mode 1. Modes 2/3 and passive are for targeted experiments and generally need
re-writing periodically (the pyPLC `ebony` companion board does this); a one-shot `WRM1` write also works.

### 6.2 Status block (`GST1` build tag + `RDM1` read)

A 80-byte status block lives at RAM `0x22c2a8` (magic `'EBS1'`, layout 1), refreshed every 100 ms. Read it with
five 16-byte `RDM1` reads. Key fields:

| Offset | Field | Meaning |
|---|---|---|
| 0x06 | build | firmware build number (159) |
| 0x08 | uptime_ms | time since power-on (hardware counter, survives firmware restarts) |
| 0x0c/0x10/0x14/0x18 | t_join / t_sdp / t_learned / t_first_resp | join & learning milestones (uptime ms; 0 = not yet) |
| 0x1c/0x1d | own / cco | live OWN_TEI (flips during V2G) / charger CCo TEI |
| 0x1e/0x1f | assoc / fsm | `0x0f` = not associated; fsm 8 = joined |
| 0x20/0x21/0x22 | teiA / teiB / nat_own | charger TEI / **car TEI** / sniffer's own real TEI (0 = not learned) |
| 0x23 | cands | car candidates at the last lookup (1 expected; >1 = highlight) |
| 0x2c/0x2e | tcp_to_charger / tcp_to_car | V2G TCP data frames caught each way |
| 0x30 | frames | all frames through the receive hook |
| 0x38/0x3a | sdp_req / sdp_resp | SDP requests / responses caught |
| 0x3c | seq | +1 per 100 ms since the last firmware start (a drop = the modem restarted) |
| 0x40/0x42 | rejected_mme / last_rejected_mmtype | stray host MMEs safely dropped (0 is normal) |
| 0x44 | learn_src | how the car TEI was found: 1 = SDP request, 2 = per-frame retry, 3 = tick fallback |
| 0x4d | mode | the mode the firmware's tick currently sees (0..3) |

A full field-by-field table and the derived values worth showing (learning timing, liveness, health flags) are
in [`patch_explanation_v159.md`](patch_explanation_v159.md) §5.

### 6.3 Memory read / write (`RDM1` / `WRM1`)

`RDM1` reads 16 bytes from a given address; `WRM1` writes one byte or word and reads the result back. They are
debug aids (the status block and mode byte are read/written through them). Only addresses in the firmware's
mapped RAM answer; others are refused.

## 7. Known gaps (help us test these)

- **Car-TEI lookup is bench-proven, not yet field-proven.** The station-table lookup worked in 3/3 bench
  sessions and against a second active sniffer, but a release goal is to confirm it on real chargers that
  assign unusual TEIs. If a session gives you SLAC but no unicast SDP/V2G, please capture the status block
  (`teiA`/`teiB`/`cands`/`learn_src`) and open an issue.
- **Odd chargers may still perturb.** On some chargers (e.g. certain Alpitronic units) the interaction between
  the sniffer and the charger's modem at the hardware level is not yet fully characterised. Report any session
  the sniffer appears to disturb.
- **Switch-register GET_SW sub-modes** (if referenced in the internals doc) are not functional on this firmware
  and are debug-only; they do not affect capture.

## Licence

Published under pyPLC's GPLv3. The patch is distributed as records of this project's own new bytes plus this
script; no vendor firmware is redistributed.
