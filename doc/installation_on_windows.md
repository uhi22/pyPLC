# Installation on Windows10

1. Install python (windows automatically launches the installer if you type „python“ into the search field of the task bar)
2. Install Wireshark, this includes the pcap driver, which is necessary for low-level-network-interaction
3. Install git (recommended, but not necessary if you get the sources from git on an other way, e.g. via zip download)
4. Install mingw32 (if not included in the git installation)

5. Install python libraries
Attention: There are (at least) three different python-libs available for pcap:
-	Libpcap
-	Pylibpcap (But: only Python2)
-	Pypcap (recommented on https://stackoverflow.com/questions/63941109/pcap-open-live-issue)
-	Pcap-ct (https://pypi.org/project/pcap-ct/)
We use the last one.
    python -m pip install --upgrade pcap-ct
This is fighting against the Libpcap-installation, so we need to deinstall the second:
    python -m pip uninstall libpcap
Then again install pcap-ct, and finally add in the libpcap\_platform\__init__py the missing is_osx = False. (Is in the meanwhile fixed in the github repository.)

6. Clone the two github repositories, and compile the OpenV2Gx EXI decoder/encoder:
Create or use a folder, where you want to store the tools, e.g. C:\myprogs\ and open a command prompt there.
```
    git clone http://github.com/uhi22/pyPlc
    git clone http://github.com/uhi22/OpenV2Gx
    cd OpenV2Gx\Release
    mingw32-make all
```

(this may take some minutes)

Test the EXI decoder/encoder
```
	cd myprogs\OpenV2Gx\Release
	OpenV2G.exe DD809a0010d0400000c800410c8000
	OpenV2G.exe EDB_5555aaaa5555aaaa
```
This should run without error and show the decoded/encoded data in the command window.

Now we go to the python part.
```
	cd $home/myprogs/pyPlc
```

Check python version

`python --version`
reports e.g. 3.9.2.

7. Edit the configuration file
The file pyPlc.ini can be changed in a way to fit the needs. E.g. the default behavior (PevMode or EvseMode) can be configured,
for the case that the pyPlc script is called without command line arguments.

8. Edit the MAC of the network interface
(Not clear, whether this is still needed. Todo: optimize code and description...)
Find out the MAC address of the laptops ethernet interface, by running `ipconfig -all` in the command line.
Edit the file addressManager.py and write your MAC into the MAC_LAPTOP variable.

9. Perform a simulated charging session
Open two command line windows.
In one command line, start the charger (EVSE) in simulation mode: `python pyPlc.py E S`.
In the other window, start a car (PEV) in simulation mode: `python pyPlc.py P S`.
Each of it should show a window where we can see how the charging works.

10. Perform a real charging session
If you have set the intended mode in the pyPlc.ini, simply call `python pyPlc.py`.

## Driver for the USB-to-Serial brigde

(This is optional and only necessary, if devices like Dieter or display is planned to be used on a USB-to-serial converter.)
For the USB-to-Serial bridge, which is sold as CP2102, the Windows 10 tries to install the driver when plugged-in. But
the device did not work together with the driver which windows found automatically. A root cause may be, that the
device is not an original CP2102, but a clone. Finally found a driver on https://www.pololu.com/docs/0J7/all, which works.

