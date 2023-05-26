# Installation on Raspberry Pi

Pitfall: Pcap-ct does not work with Python 3.4. After update to Python 3.8, it works.

To try out, we use an old raspberry pi (first generation).

Install an image on a fresh 16GB SD card, using the Raspberry Pi Imager from https://www.raspberrypi.com/software/.
Surprise: The imager does not ask for the model of the Raspberry. It just works on the old model. Fine.

In the Imager, we enable the SSH, this makes it possible to work remote on the raspberry.

On PC, we install putty, so that we are able to open an remote shell.

Start putty and connect to the raspberry.

Install samba server on the raspberry, to be able to access the files from remote. https://www.elektronik-kompendium.de/sites/raspberry-pi/2007071.htm

Install wireshark
```
	sudo apt-get install wireshark
```
Choose "yes" for the question whether other users shall be able to trace network traffic.

Install tcpdump, to be able to log the network traffic in background:
```
    sudo apt-get install tcpdump
```


Clone the two github repositories, and compile the OpenV2Gx EXI decoder/encoder:
```
	cd $home
	mkdir myprogs
	cd myprogs
	git clone http://github.com/uhi22/pyPlc
	git clone http://github.com/uhi22/OpenV2Gx
	cd OpenV2Gx/Release
	make
```
(this may take some minutes)
(In case you later change something in the code, use `make all` to build again.)

Test the EXI decoder/encoder
```
	cd $home/myprogs/OpenV2Gx/Release
	./OpenV2G.exe DD809a0010d0400000c800410c8000
	./OpenV2G.exe EDB_5555aaaa5555aaaa
```
This should run without error and show the decoded/encoded data in the command window.

Now we go to the python part.
```
	cd $home/myprogs/pyPlc
```

Check python version

`python --version`
reports e.g. 3.9.2.

Install the python library for accessing the network interface.
Also for the superuser (otherwise the import pcap fails).

```
	python -m pip install --upgrade pcap-ct
	sudo python -m pip install --upgrade pcap-ct
```

Try-out whether the python is able to sniff ethernet packets:
```
	cd $home/myprogs/pyPlc/tests
	python test_pcap.py
```
Result: Fails due to missing permission. This is normal, we need to run with superuser permissions.
```
	sudo python test_pcap.py
```
This should run through loops 0 to 9.

Try-out the cooperation of Python with the EXI encoder/decoder:
```
	python exiConnector.py
```
This should run some decoder/encoder tests and report in the end "Number of fails: 0".

Copy the pyPlc.ini.template into the same directory where pyPlc.py is, and rename it to pyPlc.ini. Edit the settings in this file as you need.

Make some files executable:
```
    chmod 744 c55*
    chmod 744 pevNoGui.py
    chmod 744 starter.sh
```

As first test, use the simulation mode (no need for modems or other hardware).
Start the EVSE in simulation mode `sudo python pyPlc.py E S`.
Open a second console window, and start here the pev in simulation mode
`sudo python pyPlc.py P S`.
We should see how the EVSE and PEV are talking to each other.

## Sudo-less run of pyPLC

The access to the ethernet raw data requires sudo. To avoid this, the following setting may help:
- Find out the path of python: `which python`. This gives something like /usr/bin/python
- Find out the "real" name of the python. The above /usr/bin/python may be a link, but we need the location where it points to.
`ls -al /usr/bin | grep python`. This shows e.g. that python is a link to python3, and python3 is a link to python3.9, and this is the real file.
- Give python the permission to access the raw ethernet traffic, e.g. `sudo setcap cap_net_raw,cap_net_admin=eip /usr/bin/python3.9`
(discussed in https://github.com/SmartEVSE/SmartEVSE-3/issues/25#issuecomment-1563519025)
- When this was done, the `python pyPlc.py E` etc work without `sudo`.

## Auto-start of the PEV software

Use case: You use a RaspberryPi in the car, and want to start the charging software just by powering-up the Raspberry.

(Based on https://gist.github.com/emxsys/a507f3cad928e66f6410e7ac28e2990f)

We want to run the pevNoGui.py as superuser automatically after startup. To achieve this, we create a service, which we give the name "pev".

```
	cd /lib/systemd/system/
	sudo nano pev.service
```

In this file, we write the following, to configure the new service:

```
	[Unit]
	Description=The PEV.
	After=multi-user.target

	[Service]
	Type=simple
	ExecStart=/home/pi/myprogs/pyPLC/starter.sh
	Restart=always

	[Install]
	WantedBy=multi-user.target
```

Finally we configure the attributes of the service, change the starter shell file to be executable, reload the service configuration and enable and start
the service:

```
	sudo chmod 644 /lib/systemd/system/hello.service
	chmod +x /home/pi/pyPlc/starter.sh
	sudo systemctl daemon-reload
	sudo systemctl enable pev.service
	sudo systemctl start pev.service
```

To stop the service:
```
	sudo systemctl stop pev.service
```

To view the log of the service, run
- `journalctl --unit=pev` or
- `journalctl -f -u pev.service`
- `journalctl -u pev --since "5 min ago"`
To follow new messages:
- `journalctl -f`

More possibilities are shown in https://wiki.archlinux.org/title/Systemd/Journal.

The service log will grow very large, because it contains the complete communication during the charging session. To avoid filling the disk space with old logs, we may want to limit the size. One option is explained at https://got-tty.org/journalctl-via-journald-conf-die-loggroesse-definierenDo:
`nano /etc/systemd/journald.conf` and set the settings

```
	SystemMaxUse=500M
	SystemMaxFileSize=100M
```
The first value defines the overall disk space which is used by the service logs. The second value specifies the maximum size of a single log file.


The next time we power-up the pi, even without a HDMI display and keyboard connected, the OLED should show the charge progress now.
Using an RaspberryPi 3 without additional startup time optimization, the time from power-on until the start of SLAC is ~21 seconds.



### Further optimizations
To automatically create pcap network traces and log files, celeron55 developed some shell scripts, see https://github.com/celeron55/pyPLC
Concept:
* The starter.sh is started either by the user in the foreground by running c55_pev_foreground.sh, or the starter.sh is started by the
systemd, when the service is started by the user by running c55_service_pev.sh.
* The starter.sh creates a directory for the log files: pyPLC/logs
* The starter.sh defines log file names, which start with the date and time. One log file for the pyPlc itself, and one for the tcpdump.pcap.
* The starter.sh starts the tcpdump in the background, and afterwards the pyPlc.
* The stdout of the pyPlc is distributed by tee to the log file and to the console/journal.
* The pyPlc is configured to terminate when the plug is pulled.
* When the pyPlc terminates, the starter.sh stops the tcpdump.


Using environment variables for services:
https://www.baeldung.com/linux/systemd-services-environment-variables


## Disable Network Manager for the ethernet port

With standard settings, the Raspberry tries to find an internet connection on the ethernet port, this means it tries to do things like DHCP and RouterSolicitation. This procedure may disturb the communication between the PEV and EVSE. That's why it is recommended to forbid the Network Manager to care for the eth0.

Discussion: https://openinverter.org/forum/viewtopic.php?p=56342#p56342

Solution ideas: https://stackoverflow.com/questions/5321380/disable-network-manager-for-a-particular-interface or https://access.redhat.com/documentation/de-de/red_hat_enterprise_linux/8/html/configuring_and_managing_networking/configuring-networkmanager-to-ignore-certain-devices_configuring-and-managing-networking Todo: which is the correct way on the raspberry?

Further discussion:
https://openinverter.org/forum/viewtopic.php?p=56434#p56434

1. Setup a new connection in NetworkManager nmcli con add connection.interface-name eth0 type ethernet connection.id CCS
2. This created a new /etc/NetworkManager/system-connections/ something
3. Edit this file, to have
```
    [ipv4]
    method=disabled
    [ipv6]
    addr-gen-mode=stable-privacy
    method=link-local
```
4. Restart the NetworkManager
5. nmcli con up CCS
6. Check which connection the NetworkManager sees:
```
    nmcli device status
    DEVICE         TYPE      STATE         CONNECTION  
    wlan0          wifi      connected     My wifi 
    eth0           ethernet  connected     CCS        
```

If (like in uhi's case) the Raspberry says for nmcli something like "The network manager is not executed.", then this should be also fine,
because it should not disturb the communication in this case.

## Nice-to-have: Password-less SSH connection from the Windows notebook to the Pi

https://strobelstefan.org/2019/10/16/zugriff-via-ssh-ohne-passworteingabe-anmeldung-erfolgt-durch-ausgetauschten-ssh-schluessel/
- Windows: C:\Program Files\PuTTY\puttygen.exe
- Windows: store the public and private key into local drive
- Pi: create a new file in $home/.ssh, with name "authorized_keys".
- Pi: copy the public key into this file
- Windows: Putty
- enter host name of the Pi
- in connection->Data, enter user name (default: pi)
- in connection->SSH->Auth, browse to the private key generated above.
- in session, give a name for the session, and click "safe" to store the connection settings
- next time, the connection to the pi works just by clicking the saved session.
