#!/usr/bin/env python3
"""Identify whether a TL-PA4010P V2 modem is running the pyPLC AR7420 sniffer build or stock firmware.

The sniffer keeps the stock version string, so `plctool -r` still shows 1.1.0.844 and cannot tell the sniffer
from stock firmware. This reads the sniffer's own build tag over its diagnostic MME instead.

Linux only; needs root (raw socket) and the modem on the given interface. Contains no vendor firmware.

Usage:  sudo python3 identify_ar7420_firmware.py <iface> <modem-mac>
        e.g. sudo python3 identify_ar7420_firmware.py eth0 f4:f2:6d:b8:2c:5e
Prints the 16-char tag (YYMMDD-Vnnn-0844) on success, or 'no sniffer tag' if the modem is stock/unreachable.
"""
import socket, struct, sys, time

def main():
    if len(sys.argv) != 3:
        sys.exit("usage: sudo python3 identify_ar7420_firmware.py <iface> <modem-mac>")
    iface, mac = sys.argv[1], sys.argv[2].lower()
    dst = bytes.fromhex(mac.replace(":", ""))
    s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(3))
    s.bind((iface, 0)); own = s.getsockname()[4]
    f = bytearray(60)
    f[0:6] = dst; f[6:12] = own; f[12:14] = b"\x88\xe1"
    f[14] = 0; struct.pack_into("<H", f, 15, 0xA000); f[17:20] = b"\x00\xb0\x52"
    f[20:24] = b"GST1"                      # sniffer build-tag request
    for _ in range(5):
        s.send(bytes(f)); t_end = time.time() + 0.5
        while time.time() < t_end:
            s.settimeout(max(0.01, t_end - time.time()))
            try: r, a = s.recvfrom(2000)
            except socket.timeout: break
            if a[2] == socket.PACKET_OUTGOING or r[12:14] != b"\x88\xe1" or r[6:12] != dst:
                continue
            if (r[15] | (r[16] << 8)) == 0xA001:
                tag = bytes(r[23:39])
                txt = bytes(c if 32 <= c < 127 else 46 for c in tag).decode()
                if txt[6:7] == "-" and "0844" in txt:
                    print("sniffer build tag:", txt); return 0
                print("replied, but no sniffer tag (stock firmware?):", txt); return 1
    print("no sniffer tag (modem stock, unreachable, or wrong interface)"); return 1

if __name__ == "__main__":
    raise SystemExit(main())
