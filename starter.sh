#!/bin/bash

date >> /home/pi/myprogs/pyPlc/test2.txt
pwd >> /home/pi/myprogs/pyPlc/test2.txt
cd /home/pi/myprogs/pyPlc/
/usr/bin/python /home/pi/myprogs/pyPlc/starter.py
pwd >> /home/pi/myprogs/pyPlc/test2.txt
date >> /home/pi/myprogs/pyPlc/test3.txt
