# Testing and Simulation

The purpose of the pyPlc project is, to talk to a real charger or to a real car. But these scenarios
have a certain effort to be tested.
To have better testing possibilities "on the desk", the following methods can be used.

## Simulation without any modem or other hardware
This works on Windows10, and should also work on Raspberry (not tested).
Open two console windows. In one window, start the pyPlc in EvseMode and simulation enabled:
```
python pyPlc.py E S
```
In the other console window, start pyPlc in PevMode and also simulation enabled:
```
python pyPlc.py P S
```

## Use two different machines
Use two machines (can be a Windows10 and a Raspberry for instance) and connect them with appropriate configured modems.
On one machine, run the charger side:
```
python pyPlc.py E
```
On the other machine start pyPlc in PevMode:
```
python pyPlc.py P
```
Wireshark can be used on any side, to make a trace of the communication for later inspection.

## Automatic Test Case execution
The above simulation environment is nice to test the standard charging process, but also the error cases should be
tested, to ensure a convinient and safe operation. For such tests, the pyPlc project contains the possiblity to
inject faults into the normal procedure, and so to test the reaction in case of errors.

### How does this work?

The main test functionality is contained in mytestsuite.py. Here the test cases are configured.
The Evse state machine triggers the selection of the next test case by calling testsuite_choose_testcase().
In the interesting points in the state machines, where we want to inject faults, we call the testsuite_faultinjection_is_triggered() inside an if condition. This function returns True, if the fault injection is triggered.

The state machine which shall be tested (can be on an other machine) reports certain execution pathes via UDP syslog messages. Based on this feedback, the testsuite decides whether the expected behavior is fulfilled or not.

### Turning the Testsuite on and off

The testsuite feature can be enabled by setting testsuite_enable = Yes in the pyPlc.ini.

### Inspecting the test results

The progress of the tests and their result can be seen in Wireshark, by applying a display filter for "syslog".
Also a test report file (testresults.txt) is created in the pyPlc main directory.

