# AR7420 sniffer firmware v159 — patch explanation

A reference description of what `patch_ar7420_sniffer_v159.py` changes in the stock **TP-Link
TL-PA4010P V2** firmware (`1.1.0.844`, Qualcomm AR7420), focused on what v159 adds over the earlier
**v142** build. Read [`patch_explanation_v142.md`](patch_explanation_v142.md) first for the base feature
set (F1–F16: the receive hook, warm NMK/NID join, learning-switch off, per-frame TEI ping-pong, the
GET_SW dispatcher); this document does not repeat it.

Companion to [`README_ar7420_sniffer_v159.md`](README_ar7420_sniffer_v159.md) (how to build and flash) and
`patch_ar7420_sniffer_v159.py` (the patch itself).

> **No vendor code here.** This document gives patch *roles* and the addresses of **this project's own**
> RAM blocks and stubs. It does not reproduce TP-Link/Qualcomm firmware bytes or disassembly — exactly as
> the patch script ships only this project's own changed bytes (291 records, 10506 bytes). The definitive
> byte-level map is those records.

---

## 1. What v159 is, in one paragraph

v159 is the v142 transparent sniffer with a **correct car-TEI determination**, a **crash-proof management-
message path**, the **per-frame TEI switching hidden from the modem's own transmit/ACK path** (so the
sniffer no longer perturbs the live session), **four operating modes**, and a **readable status block**. It
boots in ping-pong mode and, with no interaction, forwards the full SLAC + SDP + V2G session to the host —
the same user-facing behaviour as v142, minus v142's dependence on the network using TEIs {1, 2, 3}.

## 2. Base, method and layout

- **Base image:** stock `MAC-7420-v1.1.0-01-X-FINAL.nvm` (`1.1.0.844`). The runtime is an LZMA-packed ARM
  image that loads at `0x208400`. Addresses are **runtime load addresses** unless marked *(run)*.
- **Method:** identical to v142 — new code is placed in reclaimed/dead firmware regions and in free space,
  and the classifier/tick/GET_SW call sites are redirected to it. The ITCM run-vs-load caveat from v142
  §2 still applies (the F5 classifier hook at `0x27ce84` is encoded from its **run** address `0x11d70`; a
  disassembler anchored at the load address resolves the branch `0x26b114` too high — this is why a naive
  decode points at `0x498a84`, which is not a real target).
- **Build composition.** v159 is produced by layering this project's build steps (`tools/build_v159_*.py`
  over v158 → v157 → v155/v154/v152/v151/v150/v149/v148/v147/v146/v145/v143 → v133). Each step is one of
  the features in §3.

## 3. Feature delta over v142

| Area | v142 | v159 |
|---|---|---|
| Car-TEI determination | arithmetic `6 − CCo − own` (only valid for TEIs {1,2,3}) | **station-table lookup** at the SDP request, `CC_SET_TEI_MAP.IND` parse, and a tick fallback/relearn (§4.1) |
| Stray host MMEs | some restart the modem (recycled handler space) | **rejected and counted** (§4.2) |
| Effect on the live session | per-frame OWN_TEI flip reaches the modem's TX/ACK path | flip **hidden from software consumers of OWN_TEI** (§4.3) |
| Operation | on/off (`armed`) | **four modes** passive / ping-pong / selfIsCar / selfIsCharger (§4.4) |
| Observability | none (RDM1 only) | **status block** at `0x22c2a8`, 80 B, refreshed 100 ms (§5) |

Everything else (the receive hook, warm join, learning-switch off, parser cap, retry limit, build tag) is
carried from v142 unchanged.

## 4. The new/changed functions

### 4.1 Car-TEI determination (replaces v142's F1/F8 arithmetic)

v142 computed the car's TEI as `6 − CCo − own`, correct only when the three stations are TEIs {1, 2, 3}. In
the field (e.g. a Supercharger assigning the car TEI 10) the rule failed and no unicast was routed. v159
determines the car's TEI from the modem's own data instead, in three cooperating ways:

- **Station-table lookup** (the primary path, from build step v145): at the SDP request the sniffer walks
  the firmware's AVLN station table (globals `0x8edd0` / `0x8f240`; each entry carries a millisecond time
  stamp) and takes the **youngest** station that is neither the CCo nor the sniffer's own real TEI. v144
  measurement showed the car's entry present and 0–1 ms old at the SDP request in 3/3 sessions.
- **`CC_SET_TEI_MAP.IND` parse** (build step v143, MMTYPE `0x003a`): the CCo's TEI→MAC map gives an
  additional car-TEI signal; the sniffer identifies its own entry by its own MAC (not by OWN_TEI, which the
  ping-pong overwrites).
- **Tick learn + relearn** (build step v157): learning runs on the 10 Hz tick even before the first routed
  frame; a leaky-counter re-check corrects `teiB` if a younger, consistent candidate appears. The firmware
  makes the first ping-pong flip itself once the TEIs are known (no trigger frame, no host write).

The learned TEIs are published in the status block (`teiA`, `teiB`, `nat_own`, `learn_src`, `cands`).

### 4.2 Crash-proof management-message path (build step v147)

v142 reclaimed several stock MME-handler regions for its own RAM/stubs, but the stock MME dispatcher still
routed a few host-side message types into that recycled space, restarting the modem (`CM_GET_KEY` did this
on intermediate builds). v159 intercepts those dispatcher entries with a reject stub that drops the message
safely and counts it: status block `rejected_mme` (+0x40) and `last_rejected_mmtype` (+0x42). `0` there is
the normal state.

### 4.3 Per-frame TEI flip hidden from the modem's own path (build steps v149–v155)

The transparent sniffer must flip the hardware RX filter's accepted TEI per frame, but in v142 that same
value (`OWN_TEI`, stock RAM `0x8bdec`) was also read by ~11 firmware consumers, so the modem could transmit
or acknowledge under the *foreign* TEI — a plausible way to disturb a real charging session. v159 routes
every software consumer the static analysis found to read the sniffer's **real** TEI (`nat_own`) instead of
the per-frame value; only the hardware MAC RX filter (out of software reach) still follows the flip. This
keeps the sniffer passive to the car↔charger session.

### 4.4 Four operating modes (build steps v158/v159)

The v142 `armed` byte (ping-pong control block `+0x0c`, RAM `0x22c4f8`) becomes a **mode** byte:

| Value | Mode | Behaviour |
|---|---|---|
| 0 | passive | OWN_TEI held = `nat_own`; learning continues; no routing |
| **1** | ping-pong (**boot default**) | per-frame flip → full transparent capture; firmware makes the first flip |
| 2 | selfIsCar | once learned, holds OWN_TEI = `teiB` |
| 3 | selfIsCharger | once learned, holds OWN_TEI = `teiA` |
| >3 | treated as passive | |

v159's only change over v158 is to **suspend the re-check (C5) in mode 2**: in selfIsCar the sniffer holds
OWN_TEI = `teiB`, so the car's own frames carry `STEI == OWN_TEI` and the MAC drops them as its own; the
car's station-table stamp then stops refreshing and the re-check would otherwise drift `teiB` onto another
station. The mode the firmware's tick currently sees is mirrored to status block `+0x4d`.

Set the mode with the `WRM1` sub-mode (width 1) to `0x22c4f8`. For a plain capture, leave it at the default.

## 5. Status block, layout 1 (`0x22c2a8`, 80 bytes, magic `'EBS1'`)

Refreshed every 100 ms; read as five 16-byte `RDM1` reads. `magic == 0` means not yet refreshed (first
100 ms after a start). Decode only fields below `size` (+0x05).

| Offset | Type | Name | Meaning |
|---|---|---|---|
| 0x00 | u32 | magic | `'EBS1'` (`0x31534245`); 0 = not refreshed yet |
| 0x04 | u8 | layout | 1 |
| 0x05 | u8 | size | 80 |
| 0x06 | u16 | build | 159 |
| 0x08 | u32 | uptime_ms | time since power-on (hardware counter; survives firmware restarts; wraps ~49.7 days) |
| 0x0c | u32 | t_join | uptime ms this join was first seen; 0 = not joined |
| 0x10 | u32 | t_sdp | uptime ms learning started at the SDP request |
| 0x14 | u32 | t_learned | uptime ms the car TEI became known |
| 0x18 | u32 | t_first_resp | uptime ms of the first caught SDP response this join |
| 0x1c | u8 | own | OWN_TEI live (flips between teiA/teiB during V2G) |
| 0x1d | u8 | cco | CCo (charger) TEI |
| 0x1e | u8 | assoc | `0x0f` = not associated, else associated |
| 0x1f | u8 | fsm | association state (1→3→4→8; 8 = joined) |
| 0x20 | u8 | teiA | charger TEI learned (0 = not learned) |
| 0x21 | u8 | teiB | **car TEI learned** (0 = not learned) |
| 0x22 | u8 | nat_own | the sniffer's own real TEI |
| 0x23 | u8 | cands | car candidates at the last lookup (1 expected; >1 = highlight) |
| 0x24..0x29 | u8 | found_at_sdp / miss_at_sdp / found_by_retry / pending / retry_misses / clears | learning diagnostics |
| 0x2a | u8 | n_stations | stations in the modem's table (includes the sniffer while ping-pong runs → 3 in a normal session) |
| 0x2b | u8 | max_tei | highest TEI in the table |
| 0x2c | u16 | tcp_to_charger | V2G TCP data frames caught towards the charger |
| 0x2e | u16 | tcp_to_car | V2G TCP data frames caught towards the car |
| 0x30 | u32 | frames | all frames through the receive hook |
| 0x34 | u32 | (internal) | do not display |
| 0x38 | u16 | sdp_req | SDP requests (low 16 bits) |
| 0x3a | u16 | sdp_resp | SDP responses caught (low 16 bits) |
| 0x3c | u32 | seq | +1 per 100 ms since the last firmware start (a **drop** = the modem restarted) |
| 0x40 | u16 | rejected_mme | stray host MMEs safely dropped (§4.2); 0 is normal |
| 0x42 | u16 | last_rejected_mmtype | MMTYPE of the last dropped one (e.g. `0x600C` = CM_GET_KEY) |
| 0x44 | u8 | learn_src | 0 none, 1 SDP request, 2 per-frame retry, 3 tick fallback; per join |
| 0x45 | u8 | c5_score | re-check counter (internal; display only) |
| 0x46 | u8 | first_flips | first flips made by the firmware's tick, since start |
| 0x47 | u8 | disarm_fixes | OWN_TEI put back to nat_own while in passive mode, since start |
| 0x48 | u8 | sdp_seen | 1 = an SDP request was seen this join |
| 0x49 | u8 | relearns | car TEI corrected by the re-check, since start |
| 0x4a | u8 | cand_age | ticks a car candidate has existed (255 = saturated); per join |
| 0x4b..0x4c | - | (internal) | do not display |
| 0x4d | u8 | mode | 0 passive, 1 ping-pong, 2 selfIsCar, 3 selfIsCharger (as the tick saw it) |
| 0x4e..0x4f | - | reserved | 0 |

**Derived values worth showing**
- **Learning state:** `teiB != 0` → car TEI = teiB (charger teiA, own nat_own); `pending == 1` → car not
  found yet (fallback); both 0 → waiting for the SDP request.
- **Learning timing:** `t_sdp − t_join`, `t_learned − t_join`, `t_first_resp − t_join` (100 ms resolution).
  Bench (1 sniffer): SDP ~0.8 s, learned ~0.8 s, first response ~0.9 s after the join.
- **Restart detection:** time since last restart = `seq / 10` s; a `seq` drop between reads = a restart (the
  CCo-left reset in a field-like session does this). **Liveness:** `seq` rises ~5 over 0.5 s.
- **Health flags to highlight:** `miss_at_sdp > 0`, `cands > 1`, or `rejected_mme > 0`.

The network key (`NMK`, 16 B at `0x8ba30`) is readable by one `RDM1` read but is **sensitive** — show it
only blurred, never log it, never export it.

## 6. GET_SW diagnostic request/response format

The sub-channel rides on the vendor `VS_SW_VER` (GET_SW) MME, EtherType `0x88E1`, OUI `00 b0 52`. A request
with no marker falls through to the stock handler (so `plctool -r` still reports stock `1.1.0.844`). A marker
at payload offset 20 selects a sub-mode:

| Marker @20 | Sub-mode | Request fields | Reply |
|---|---|---|---|
| `GST1` | build tag | — | 16-byte tag `261018-V159-0844` |
| `RDM1` | read 16 B | address u32 LE @24 | the 16 bytes at that address |
| `WRM1` | write | address @24, width @28 (use 1), data byte @29 | `RDM1`-shaped reply: the 16 bytes at the address, read back after the write |

Only firmware-mapped RAM answers; other addresses are refused. One GET_SW request outstanding at a time.
`identify_ar7420_firmware.py` uses `GST1`; the pyPLC companion readers use `RDM1`/`WRM1` for the status
block and the mode byte.

## 7. Status and known gaps

- **Bench-verified (2026-10-18):** all four modes behave correctly, including with a second active sniffer on
  the network; the car-TEI lookup holds `teiB` with `relearns = 0`; the EVSE session is undisturbed
  throughout (1700+ CurrentDemandReq, no SessionStop). v159 reads back byte-identical after flashing on both
  a V2.0 and a V2.4 unit.
- **Not yet field-proven:** the station-table lookup against a wide range of real chargers (unusual TEI
  assignments) — the purpose of this draft release. Capture the status block on any failing session.
- **Odd chargers:** the hardware-level interaction with some chargers (e.g. certain Alpitronic units) is not
  fully characterised; report any session the sniffer appears to disturb.
- **Switch-register GET_SW sub-modes** are not functional on `1.1.0.844` (a debug aid only, carried from
  v142); they do not affect capture.
