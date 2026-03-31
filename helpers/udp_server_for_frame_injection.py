#!/usr/bin/env python3
"""
UDP command server — sends arbitrary raw Ethernet frames.
Command format: hex string of complete Ethernet frame
Example: "ffffffffffff112233445566 88E1 01A0380000A100000000000000000000000000000000"
         (spaces optional, ignored)
"""

import socket
from scapy.all import Ether, Raw, sendp

HOST  = "0.0.0.0"
PORT  = 5005
IFACE = "eth0"

def send_raw(hex_frame: str, count: int) -> str:
    raw_bytes = bytes.fromhex(hex_frame.replace(" ", ""))
    frame = Ether(raw_bytes)
    sendp(frame, iface=IFACE, count=count, inter=0.1, verbose=False)
    return f"OK: sent {count} frame(s), {len(raw_bytes)} bytes each"

# Warm up Scapy
print("Initializing Scapy...")
send_raw("ffffffffffff112233445566 88E1 00", 0)
print("Ready.")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))
print(f"UDP server listening on port {PORT}")

while True:
    data, addr = sock.recvfrom(65535)  # max UDP payload
    cmd = data.decode().strip()

    try:
        # Format: "COUNT HEXFRAME"
        # Example: "1 ffffffffffff112233445566 88E1 01A038..."
        parts     = cmd.split(None, 1)  # split on first space only
        count     = int(parts[0])
        hex_frame = parts[1]
        response  = send_raw(hex_frame, count)

    except Exception as e:
        response = f"ERR: {str(e)}"

    print(f"{addr[0]} → {response}")
    sock.sendto(response.encode(), addr)