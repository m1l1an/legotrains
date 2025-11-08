# Product Requirements Document

## User Interface 

For simplicity (and also because it's more hacker-like ;) we are using a text user interface, utilizing the `textual`
Python library.

We are hardcoding two trains now: FreightTrain and PassangerTrain. 

They can be controlled via simple keystrokes at any time:

FreightTrain accelerate: w
FreightTrain max speed forward: W
FreightTrain decelerate: s
FreightTrain max speed backwards: S
FreightTrain stop: x

PassangerTrain accelerate: i
PassangerTrain max speed forward: I
PassangerTrain decelerate: k
PassangerTrain max speed backwards: K
PassangerTrain stop: ,

Quit the framework: q

Screen could look like below:

+----------------+----------------------------------+----------------+
|  FreightTrain  |            Programs              | PassangerTrain |
|    <Moving>    |                                  |    <Stopped>   |
|       -5       |    Train Race                    |        0       |
|                |    Cow Scare                     |                |
|                |                                  |                |
|                |                                  |                |
|                |                                  |                |
|                |                                  |                |
+----------------+----------------------------------+----------------+
| Log messages are being printed here, e.g. FreightTrain stopped.    |
|                                                                    |
|                                                                    |
|                                                                    |
|                                                                    |
|                                                                    |
+--------------------------------------------------------------------+

## Connectivity

Should any of the trains be disconnected, the framework is continuously scanning for the Lego Hub,
using Bleak's scanner. 
We support two hardcoded hubs, FreightTrain and PassangerTrain.
Initially they are in DISCONNECTED state. Once presence is detected via Bleak scanning, we go into CONNECTING state. Once connection
is up, they will be CONNECTED.

UI will show CONNECTING or DISCONNECTED accordingly. If hub is connected, it will show the motor status.

## Programs

The student can write programs that derive from the TrainProgram class. TrainProgram auto-registers the program
to the parent with a name, so it can be listed under Programs.
The TrainProgram class stores references to the hubs, so it can control them.

On the UI, arrow keys can be used to choose and run a program, where the run() method is called.

The aim of the whole framework is for students to be able to write and test their own programs.


