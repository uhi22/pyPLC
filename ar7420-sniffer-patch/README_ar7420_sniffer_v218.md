# ISO15118 / HomePlug-AV sniffer firmware **v218** for the TP-Link TL-PA4010P V2 (QCA AR7420)

`patch_ar7420_sniffer_v218.py` turns the **official TP-Link TL-PA4010P V2 firmware (1.1.0.844)** into an
**unjoined** transparent sniffer for CCS charging. It listens to the powerline **without joining any network**,
recovers the network key of a car↔charger session from the traffic it overhears, decrypts the session inside the
modem, and forwards the decrypted SLAC, SDP and V2G traffic to its Ethernet host — so pyPLC (or Wireshark) on the
host PC sees the full charging session. Because it never joins, it is silent on the powerline: it transmits nothing
of its own.

The script is pure Python standard library, runs offline, and **contains no TP-Link or Qualcomm firmware** —
only the bytes this project changed. You supply the stock firmware yourself from a lawful copy.

> **v218 is the *unjoined* variant; the [v159 build](README_ar7420_sniffer_v159.md) is the *joined* variant. They
> live in parallel — v218 does not replace v159.**
> - **v159 (joined):** warm-joins the car↔charger network it overhears. Mature, widely bench-tested.
> - **v218 (unjoined):** never joins, decrypts in-modem, and stays silent on the powerline. Use it where the modem
>   must not appear on the network at all.
>
> Pick one; both flash the same way.

> **⚠️ Draft release for field testing.** v218 is verified on the bench (SLAC / SDP / V2G reach the host; the modem
> is silent on the powerline across many sessions) but has **not** yet been proven against a wide range of real
> chargers. **Feedback and test results are very welcome:** open a GitHub issue on this repository, or post in the
> [openinverter forum](https://openinverter.org/forum/). Please include your hardware revision, the firmware tag
> (`261110-V218-0844`), the charger model, and how reliably the session was captured.

## ⚠️ Read this first

- **Flashing can brick the modem.** Recovery may require SPI flash access (opening the case, soldering). You are
  solely responsible; there is no warranty.
- This is a **sniffer**: it recovers the key of a car↔charger session it overhears and captures **other parties'**
  SLAC/SDP/V2G traffic. Use it only on sessions and vehicles you are **authorised** to monitor.
- Supported hardware: tested on **TL-PA4010P V2.0** (AR7420) running stock firmware `1.1.0.844`. Revisions **V2.3
  and V2.4 are most likely supported too** (same `1.1.0.844` firmware) but are untested.
- The patch script accepts the input only if its SHA-256 matches the stock `1.1.0.844` `.nvm`, so firmware from any
  other version is **refused, not mis-flashed**. It is pure Python 3.

## What the sniffer does (high level)

- **Unjoined operation:** listens on the powerline without joining; the modem never associates and transmits
  nothing of its own (see *Silence on the powerline* below).
- **Forwards the SLAC handshake** (PEV↔EVSE) to the Ethernet host.
- **Recovers the session key in-modem:** overhears the network key material and the key-exchange messages of the
  car↔charger session and derives the live encryption key, with no reboot and no key of its own.
- **Decrypts the session inside the modem** and delivers the plaintext IPv6 (SDP + V2G TCP) to the host
  as native Ethernet frames.
- **Delivers foreign unicast to the host:** switch MAC-learning is off and the receive filter is opened so the
  unicast SDP/V2G frames (addressed to the car's and charger's MACs) reach the host.
- **Silence on the powerline:** the modem does not announce itself (no unassociated-station announcement) and does
  not answer management messages it overhears (e.g. a charger's broadcast key-set), so it stays quiet on the wire. It still transmits frames the **host** explicitly sends through it.
- **LED status indicator** on the three front LEDs (see *LEDs* below).
- **Optional status frame** the modem can send to the host for live monitoring (see *Status frame* below); it is
  **off by default**.
- The stock version string is left unchanged; the build is identified by a separate tag over the vendor GET_SW
  diagnostic MME (see *Verify the flash*).

## 1. Get the stock firmware (you download it)

TP-Link package: <https://static.tp-link.com/resources/software/TL-PA4010PKIT_V2_130807.zip>
```text
zip  TL-PA4010PKIT_V2_130807.zip         SHA-256 191fccea7644cf0b9831d28c69bd9da63745ffc052a06dfb4dcb79fbc10df781
file MAC-7420-v1.1.0-01-X-FINAL.nvm      SHA-256 398f29834eaa51b0bac2ba660c74da83b6274f1ffef1400ace1c59b00f7f8d27
```
Unzip and locate `MAC-7420-v1.1.0-01-X-FINAL.nvm`.

## 2. Build the patched firmware

```sh
python patch_ar7420_sniffer_v218.py MAC-7420-v1.1.0-01-X-FINAL.nvm -o ar7420_sniffer_v218.nvm
```
The script verifies the input SHA-256, applies the patch, and verifies the output SHA-256:
```text
output ar7420_sniffer_v218.nvm           SHA-256 db0e9fe5ef91ab572065207ffd8f79c0256b4e077a12eb1db69aaf975bf0150b
```
If either hash does not match it stops and writes nothing.

**If the *output* SHA-256 does not match** (the input matched, but the script reports an output mismatch and writes
nothing): the patch is applied correctly, but your Python rebuilt the compressed image slightly differently. The
script uses the standard-library LZMA compressor, and a different Python/zlib-liblzma build can produce a
byte-different (but functionally identical) stream. This build's hash was produced on Python 3 on Windows 10 /
Raspberry Pi OS. If you hit this, try a stock CPython 3 on Linux (or Raspberry Pi OS), and please report it — with
your OS and `python3 --version` — on a GitHub issue or the [openinverter forum](https://openinverter.org/forum/), so
the reference hash can be checked across platforms. Do **not** flash an image the script refused to write.

## 3. Flash it over Ethernet (with YOUR OWN modem config)

Needs [open-plc-utils](https://github.com/qca/open-plc-utils) (`plctool`). **No PIB is shipped** — you supply your
modem's PIB so its MAC/keys are preserved:
```sh
# 1. back up your current PIB
plctool -i <iface> -p my_backup.pib <modem-mac>
# 2. write firmware + PIB, then reset
plctool -i <iface> -P my_backup.pib -N ar7420_sniffer_v218.nvm -R <modem-mac>
```
After the reset the modem runs the sniffer build. Point pyPLC / Wireshark at the host interface.

**Capture on a promiscuous-capable interface.** The sniffer forwards unicast SDP/V2G frames addressed to the car's
and charger's MACs, not the host's. A NIC that filters by destination MAC (many built-in laptop ports do) shows the
broadcast/multicast SLAC but drops the unicast — making it look like forwarding is broken when it is not. Capture
with a promiscuous-capable adapter (a USB Ethernet dongle is reliable); `tcpdump` and Wireshark enable promiscuous
mode by default, a raw socket in your own script does not. If you see SLAC but no SDP/V2G, suspect the capture
interface first.

**PIB (required):** like v159, this build was tested only with a PIB in the **PEV role** — the same modem
configuration pyPLC uses for its adapters. All bench testing used a PEV-role PIB; a non-PEV PIB is untested, and an
EVSE-role PIB in particular makes the modem act as the network coordinator, which is the opposite of the quiet,
unjoined behaviour this build is for. If your modem's PIB is not already a PEV PIB, set one up with pyPLC's
[step-by-step PIB setup](https://github.com/uhi22/pyPLC#step-by-step) and flash the sniffer firmware together with
*that* PIB in the command above.

## 4. Verify the flash

The patch deliberately **keeps the stock version string**, so `plctool -r` still reports `1.1.0.844` and cannot tell
the sniffer from stock firmware. Confirm the sniffer build with the included reader (Linux, root):
```sh
sudo python3 identify_ar7420_firmware.py <iface> <modem-mac>
# -> sniffer build tag: 261110-V218-0844
```
Seeing the tag means the sniffer firmware is running; `no sniffer tag` means the modem is still stock (or
unreachable / wrong interface).

## 5. Roll back

Re-flash the stock firmware the same way:
```sh
plctool -i <iface> -P my_backup.pib -N MAC-7420-v1.1.0-01-X-FINAL.nvm -R <modem-mac>
```

## LEDs

The three front LEDs show the sniffer state (no tool needed):

| LED | Meaning |
|---|---|
| **Power** | **solid** = quiet powerline (no HomePlug beacon for ≥ 200 ms) · **flickering** = beacons are being heard (a network is active nearby) |
| **PLC** | **off** = nothing learned yet · **slow blink** (≈ 500 ms) = the network key has been overheard · **fast blink** (≈ 160 ms) = the session key has been recovered and decryption is live |
| **Ethernet** | **one short flash** (≈ 40 ms) per decrypted IPv6 frame delivered to the host |

At power-up all three LEDs light together for about one second as a lamp test.

A normal capture looks like: power flickering (beacons), PLC fast-blinking (key recovered), Ethernet flashing as
frames flow to the host.

## Status frame (optional, for live monitoring)

The modem can send a small **status frame** to the host every **250 ms**, carrying live counters (uptime, how many
key messages were seen, how many frames were shipped, beacon/SOF/SACK counts). It is **off by default** — a modem
with no monitor stays silent — and it is enabled by the host writing one byte over the vendor GET_SW diagnostic MME.

The status frame is wire-compatible with the QCA7000 sniffer's status frame, so one decoder reads both (they differ
only by `LAYOUT_VER`).

### Turning it on and off

Write one byte at address `0x00233838` over GET_SW with the `WRM1` marker, width 1:

- value **`1`** → the modem sends the status frame every 250 ms;
- value **`0`** → the modem stops sending it (this is also the power-on default).

The byte lives in RAM, so **every firmware start (power-on, reset, the per-session reset) returns it to 0**. A host
that wants the status frame should re-enable it when it has seen no status frame for about a second.

`WRM1` wire format (vendor VS_SW_VER.REQ, MMTYPE `0xA000`, unicast to the modem's MAC):

| Offset | Bytes | Value |
|---|---|---|
| 20 | 4 | marker `WRM1` (ASCII) |
| 24 | 4 | address, little-endian = `0x00233838` |
| 28 | 1 | width = `1` |
| 29 | 1 | the data byte (`0x01` to enable, `0x00` to disable) |

The reply (MMTYPE `0xA001`) carries the 16 bytes read back from that address; its first byte is the value now in
force, which confirms the write.

### Frame structure

- **EtherType** `0x88E1` (HomePlug AV), **MMV** `0x00`, **MMTYPE** `0x0000`.
- **Destination MAC** is **broadcast** (`ff:ff:ff:ff:ff:ff`); the source MAC is the modem's own MAC. Filter on the
  source MAC plus the magic below.
- The payload (first byte right after the 2-byte MMTYPE, i.e. at Ethernet-frame offset 17) is a block of **13
  little-endian 32-bit fields**:

| Offset | Field | Meaning |
|---|---|---|
| 0 | `MAGIC` | the four ASCII bytes `S` `T` `A` `T` (`0x54415453` little-endian) |
| 4 | `LAYOUT_VER` | `8` for this (AR7420 unjoined) build; the QCA7000 build uses `7` |
| 8 | `SEQ` | increments by 1 per frame since the last firmware start |
| 12 | `UPTIME_MS` | milliseconds since power-on (free-running hardware counter) |
| 16 | `SEEN` | encrypted-payload messages seen on the key-recovery path |
| 20 | `CNFCNT` | key-confirm messages recognised |
| 24 | `OKCNT` | session key successfully installed (decryption live) |
| 28 | reserved | `0` |
| 32 | `DROP` | frames dropped on the host-delivery path |
| 36 | `BEACON` | HomePlug beacons counted |
| 40 | `SOF` | start-of-frame delimiters counted |
| 44 | `SACK` | selective-acknowledge delimiters counted |
| 48 | `SHIP` | decrypted IPv6 frames delivered to the host |

All counters are relative to the last firmware start; show them as rates (delta per second) or as growing totals.
`SEQ` dropping back means the modem restarted.

## Licence

Published under pyPLC's GPLv3. The patch is distributed as records of this project's own new bytes plus this script;
no vendor firmware is redistributed.
