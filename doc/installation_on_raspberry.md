# Installation on Raspberry Pi

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


Start the EVSE `sudo python pyPlc.py E`.
Open a second console window, and start here the pev in simulation mode
`sudo python pyPlc.py P S`.
We should see how the EVSE and PEV are talking to each other.

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
	ExecStart=/home/pi/myprogs/myPlc/starter.sh
	Restart=on-abort

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
