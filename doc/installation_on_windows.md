# Installation on Windows10

## Driver for the USB-to-Serial brigde

For the USB-to-Serial bridge, which is sold as CP2102, the Windows 10 tries to install the driver when plugged-in. But
the device did not work together with the driver which windows found automatically. A root cause may be, that the
device is not an original CP2102, but a clone. Finally found a driver on https://www.pololu.com/docs/0J7/all, which works.

