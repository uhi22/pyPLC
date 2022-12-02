
# For serial (including USB-to-serial) interfaces:
# https://pyserial.readthedocs.io/en/latest/pyserial.html
# Install pyserial library:
#   python -m pip install pyserial
# List ports:
#   python -m serial.tools.list_ports

import serial # the pyserial
from serial.tools.list_ports import comports
from time import sleep

if __name__ == "__main__":
    nFail=0
    print("Testing hardwareInterface...")
    print('Available ports:')
    ports = []
    for n, (port, desc, hwid) in enumerate(sorted(comports()), 1):
        print('{:2}: {:20} {!r}'.format(n, port, desc))
        ports.append(port)
    if (len(ports)<1):
        print("no ports, we cannot test anything.")
        exit()
    print("ok, we take the first port, " + ports[0])
    ser = serial.Serial(ports[0], 19200, timeout=0)
    for i in range(0, 5):
        ser.write(b'hello world\n')
        sleep(0.5)
        s = ser.read(100)
        if (len(s)>0):
            print(str(len(s)) + " bytes received: " + str(s, 'utf-8'))
    ser.close()
    print("finished.")