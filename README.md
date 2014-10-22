MavLink Serial To UDP
==================

This is to send  MavLink data from a APM or Pixhawk to a GCS via a Raspberry PI using UDP.
To run the script:
python MavLinkSerialToUDP.py /dev/ttyAMA0 57600  10.0.0.101 14550

Script will wait for connect from mission planner but will not reconnect if connection is closed.
