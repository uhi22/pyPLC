# ISO15118 / HomePlug-AV sniffer firmware for the TP-Link TL-PA4010P V2 (QCA AR7420)

> **⚠️ Older build — v159 is now available.** For new field tests use
> [`README_ar7420_sniffer_v159.md`](README_ar7420_sniffer_v159.md). v159 is a drop-in replacement with the
> same transparent behaviour out of the box, plus a correct car-TEI lookup (v142 only works when the network
> uses TEIs {1, 2, 3}), a crash-proof management-message path, and a readable status block. This v142 document
> is kept for reference.

`patch_ar7420_sniffer_v142.py` turns the **official TP-Link TL-PA4010P V2 firmware (1.1.0.844)** into a
transparent sniffer for CCS charging. It overhears the SLAC handshake between a car and a charging station,
joins the HomePlug-AV network those two set up, and forwards all SLAC, SDP and V2G traffic to its Ethernet
host — so pyPLC (or Wireshark) on the host PC sees the full charging session. (It does not join ordinary
home powerline networks; it keys itself only to the car↔charger network it learns from the SLAC.)

The script is pure Python standard library, runs offline, and **contains no TP-Link or Qualcomm firmware** —
only the bytes this project changed. You supply the stock firmware yourself from a lawful copy.

> **⚠️ Draft release.** The sniffer is functionally verified (full SLAC / SDP / V2G reach the host, smoke tests
> pass), but large-scale field testing is still planned. **Feedback and test results are very welcome** — open a
> GitHub issue on this repository, or post in the [openinverter forum](https://openinverter.org/forum/). Please
> include your hardware revision, the firmware version, and how reliably the session was captured.

## ⚠️ Read this first

- **Flashing can brick the modem.** Recovery may require SPI flash access (opening the case, soldering). You
  are solely responsible; there is no warranty.
- This is a **sniffer**: from the SLAC handshake it overhears, it adopts the key of the car↔charger network
  and captures **other parties'** SLAC/SDP/V2G traffic. Use it only on sessions and vehicles you are
  **authorised** to monitor.
- Supported hardware: tested on **TL-PA4010P V2.0** (AR7420) running stock firmware `1.1.0.844`. Revisions
  **V2.3 and V2.4 are most likely supported too** (they ship the same `1.1.0.844` firmware) but are untested.
- The patch script accepts the input only if its SHA-256 matches the stock `1.1.0.844` `.nvm`, so firmware from
  any other version is **refused, not mis-flashed**. It is pure Python 3, verified byte-identical on Windows 10,
  Raspberry Pi OS, and WSL Ubuntu.

## 1. Get the stock firmware (you download it)

TP-Link package: <https://static.tp-link.com/resources/software/TL-PA4010PKIT_V2_130807.zip>
```text
zip  TL-PA4010PKIT_V2_130807.zip         SHA-256 191fccea7644cf0b9831d28c69bd9da63745ffc052a06dfb4dcb79fbc10df781
file MAC-7420-v1.1.0-01-X-FINAL.nvm      SHA-256 398f29834eaa51b0bac2ba660c74da83b6274f1ffef1400ace1c59b00f7f8d27
```
Unzip and locate `MAC-7420-v1.1.0-01-X-FINAL.nvm`.

## 2. Build the patched firmware

```sh
python patch_ar7420_sniffer_v142.py MAC-7420-v1.1.0-01-X-FINAL.nvm -o ar7420_sniffer_v142.nvm
```
The script verifies the input SHA-256, applies the patch, and verifies the output SHA-256:
```text
output ar7420_sniffer_v142.nvm           SHA-256 a9f09e619cd5f411f7d6928246649a6d5390b66a6583a61f48493ca58431ad84
```
If either hash does not match it stops and writes nothing.

## 3. Flash it over Ethernet (with YOUR OWN modem config)

Needs [open-plc-utils](https://github.com/qca/open-plc-utils) (`plctool`). **No PIB is shipped** — you supply
your modem's PIB so its MAC/keys are preserved:
```sh
# 1. back up your current PIB
plctool -i <iface> -p my_backup.pib <modem-mac>
# 2. write firmware + PIB, then reset
plctool -i <iface> -P my_backup.pib -N ar7420_sniffer_v142.nvm -R <modem-mac>
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
# -> sniffer build tag: 261008-V142-0844
```
Seeing the tag means the sniffer firmware is running; `no sniffer tag` means the modem is still stock
(or unreachable / wrong interface).

## 5. Roll back

Re-flash the stock firmware the same way:
```sh
plctool -i <iface> -P my_backup.pib -N MAC-7420-v1.1.0-01-X-FINAL.nvm -R <modem-mac>
```

## What the patch changes (high level)

- Forwarding the PEV↔EVSE SLAC to the host
- Overhearing network key from the SLAC `CM_SLAC_MATCH.CNF` to warm-join the session's network (new key/NID, no reboot)
- Switch MAC-learning off (so foreign unicast reaches the host)
- Per-frame TEI-accept flip, to route the unicast IPv6 traffic
- Shorter association-retry limit to increase the probability to catch the first SDP frame
- The stock version string is left unchanged; the build is identified by a separate tag over the vendor GET_SW diagnostic MME, using a magic pattern in the request

## Licence

Published under pyPLC's GPLv3. The patch is distributed as records of this project's own new bytes plus this
script; no vendor firmware is redistributed.
