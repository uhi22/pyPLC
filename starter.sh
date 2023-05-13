#!/bin/bash

# Function to start tcpdump
start_tcpdump() {
    INTERFACE="eth0"  # Change this to the interface you want to monitor
    OUTPUT_FILE="$1"
    tcpdump -i "$INTERFACE" -w "$OUTPUT_FILE" &> /dev/null &
    TCPDUMP_PID=$!
    echo "Started tcpdump with PID $TCPDUMP_PID on interface $INTERFACE, output file: $OUTPUT_FILE"
}
# Function to stop tcpdump
stop_tcpdump() {
    if [ ! -z "$TCPDUMP_PID" ]; then
        echo "Stopping tcpdump with PID $TCPDUMP_PID"
        kill -SIGINT "$TCPDUMP_PID"
    fi
}
# Function to handle signals
signal_handler() {
    echo "Caught signal, stopping tcpdump and exiting..."
    stop_tcpdump
    exit 1
}
# Set trap for signals: SIGINT (2), SIGTERM (15)
trap 'signal_handler' 2 15

# Todo: explain this
set -euv

# Keep all IPv6 addresses on the interface down event.
# Todo: flexible interface name.
sysctl net.ipv6.conf.eth0.keep_addr_on_down=1

# Shut down and activate the interface.
# Todo: Why this needed?
ip link set eth0 down
sleep 1
ip link set eth0 up
sleep 1

# show the addresses
ip addr

# todo: flexible path name
mkdir -p /home/pi/myprogs/pyPLC/log
# prepare the file names for the log files
date=$(date "+%Y-%m-%d_%H%M%S")
logfile=/home/pi/myprogs/pyPLC/log/"$date"_pevNoGui.log
tcpdump_logfile=/home/pi/myprogs/pyPLC/log/"$date"_tcpdump.pcap

echo "logfile: $logfile"
echo "tcpdump_logfile: $tcpdump_logfile"

# start the tcpdump
start_tcpdump "$tcpdump_logfile"

echo "$date" >> "$logfile"
git log --oneline -1 >> "$logfile" || echo "Not a git repo" >> "$logfile"
ip addr >> "$logfile"
pwd >> "$logfile"
# Todo: flexible path name
cd /home/pi/myprogs/pyPLC/
#/usr/bin/python3 /home/user/projects/pyPLC/pevNoGui.py | tee -a "$logfile"
#stdbuf -oL -eL /usr/bin/python3 /home/user/projects/pyPLC/pevNoGui.py | tee -a "$logfile"
#PYTHONUNBUFFERED=1 /usr/bin/python3 /home/user/projects/pyPLC/pevNoGui.py | stdbuf -oL -eL tee -a "$logfile"
PYTHONUNBUFFERED=1 /usr/bin/python3 /home/pi/myprogs/pyPLC/pevNoGui.py | tee -a "$logfile"
pwd >> "$logfile"
date >> "$logfile"

# Stop the tcpdump when the pyPLC stopped:
stop_tcpdump

