#!/bin/bash

# enter in the pyPLC directory, so that all subsequent pathes can be relative to this.
cd "$( dirname "${BASH_SOURCE[0]}" )"

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

#  Set options for the bash: exit on error, treat unused variables as error, print the input as it is read.
set -euv

# Keep all IPv6 addresses on the interface down event.
# Todo: flexible interface name.
# Todo: On raspberry, without NetworkManager, this option does not help. After the down and up (see below), the IPv6 is missing.
sysctl net.ipv6.conf.eth0.keep_addr_on_down=1

# Shut down and activate the interface.
# Todo: Why this needed? On raspberry, where the NetworkManager is not runnning, this disturbs, because
# afterwards the pyPlc does not see the interfaces IPv6 address.
# Todo: make this configurable, for the cases we need this.
# ip link set eth0 down
sleep 1
# ip link set eth0 up
sleep 1

# show the addresses
ip addr

# print the current directory to log. Should be the pyPLC directory.
pwd

# create directory for the log files.
mkdir -p log
# prepare the file names for the log files
date=$(date "+%Y-%m-%d_%H%M%S")
logfile=./log/"$date"_pevNoGui.log
tcpdump_logfile=./log/"$date"_tcpdump.pcap

echo "logfile: $logfile"
echo "tcpdump_logfile: $tcpdump_logfile"

# start the tcpdump
start_tcpdump "$tcpdump_logfile"

echo "$date" >> "$logfile"
git log --oneline -1 >> "$logfile" || echo "Not a git repo" >> "$logfile"
ip addr >> "$logfile"
pwd >> "$logfile"

# call the pyPlc python script
PYTHONUNBUFFERED=1 /usr/bin/python3 pevNoGui.py | tee -a "$logfile"
pwd >> "$logfile"
date >> "$logfile"

# Stop the tcpdump when the pyPLC stopped:
stop_tcpdump

