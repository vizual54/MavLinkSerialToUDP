#!/usr/bin/python

import socket
import serial
import logging
import threading
import sys
import os
import time

if ( len(sys.argv) == 1 ):
    print "MavLink Serial to UDP | Nils Hogberg, 2014"
    print "Syntax: " + sys.argv[0] + " serial_port baud_rate(=57600) udp_ip(= 127.0.0.1) udp_port(= 14550)"
    print "Example: " + sys.argv[0] + " /dev/ttyAMA0 57600 127.0.0.1 14550"
    quit()

serial_port = sys.argv[1]

if ( len(sys.argv) >= 3 ):
    baud_rate = sys.argv[2]
else:
    baud_rate = "57600"
if ( len(sys.argv) >= 4 ):
    udp_ip = sys.argv[3]
else:
    udp_ip = "127.0.0.1"
if ( len(sys.argv) >= 5 ):
    udp_port = sys.argv[4]
else:
    udp_port = "14550"

# Create a sensor log with date and time
layout = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(filename='/tmp/MavLinkSerialToUDP.log', level=logging.INFO, format=layout)

# UDP Socket
udp_port = int(udp_port)
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_socket.bind(('0.0.0.0', udp_port))
udp_socket.setblocking(0)
baud_rate = int(baud_rate)
py_serial    = None
connection = False

def open_port(portname, baudrate):
  try:
    # Set timeouts to 4 ms. 3.5 ms is the measured bias when long msg get cut!
    return serial.Serial(portname, baudrate, timeout=0.004, writeTimeout=0.004)
  except serial.SerialException as e:
    logging.debug("Could not open serial port: {}".format(portname, e))
    print ("Could not open serial port: {}".format(portname, e))
  return None
  
def ser_write(output):
    try:
      bytes = py_serial.write(output)
    except serial.SerialTimeoutException as e:
      logging.error("Write timeout on serial port")
    except serial.SerialException as e:
      logging.error("Write exception serial port")
    finally:
      py_serial.flushInput()                                             # Workaround: free write buffer (otherwise the Arduino board hangs)
	
def udp_write(msg):
    bytes = udp_socket.sendto(msg, (udp_ip, udp_port))

def udp_to_ser():                                                       # UDP to serial thread
	try:
		udp_data, udp_client = udp_socket.recvfrom(1024)            	# receive data on UDP
	except socket.timeout:
		logging.error("Read timeout on socket")
	except:
            pass
	else:
		ser_write(udp_data)                                         	# write data to serial
			
def ser_to_udp():														# Serial to UDP thread
	try:
		ser_msg = py_serial.readline().strip()                          # Remove newline character '\n'
	except serial.SerialTimeoutException as e:
		logging.error("Read timeout on serial port")
	except serial.SerialException as e:
		logging.error("Read exception on serial port")
	else:
		udp_write(ser_msg)                                              # write to UDP

def main():
    global connection
    while connection is False:
        time.sleep(1)
        udp_socket.sendto('hello', (udp_ip, udp_port))
        try:
            udp_data, udp_client = udp_socket.recvfrom(1024)
            if udp_data is not None:
                connection = True
        except:
            pass
        else:
            ser_write(udp_data)
          
    while connection is True:
            ser_to_udp()
            udp_to_ser()

print "Connecting to serial port: ", serial_port
py_serial = open_port(serial_port, baud_rate)
if py_serial is None:
    print "Could not open serial port. Script exit."
    sys.exit()
print "Waiting on port: ", udp_port
try:
    main()
except KeyboardInterrupt:
    py_serial.close()
    sys.exit(1)
