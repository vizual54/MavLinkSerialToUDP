#!/usr/bin/python

import socket
import serial
import logging
import threading
import sys
import os
import time

if ( len(sys.argv) == 1 ):
    print "MavLink UDP Proxy by Nils Hogberg, 2014"
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
		
print "Reading from serial port: " + serial_port + ":" + baud_rate
print "Sending to " + udp_ip + ":" + udp_port

# Create a sensor log with date and time
layout = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(filename='/tmp/MavLink_UDP_Proxy.log', level=logging.INFO, format=layout)

# Thread lock for multi threading
THR_LOCK = threading.Lock()

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
    #return serial.Serial(portname, baudrate, timeout=0.004, writeTimeout=0.004)
    return serial.Serial(portname, baudrate)
  except serial.SerialException as e:
    logging.debug("Could not open serial port: {}".format(portname, e))
    print ("Could not open serial port: {}".format(portname, e))
  return None
  
def ser_write(output):
  if py_serial is not None:
    THR_LOCK.acquire()
    try:
      bytes = py_serial.write(output)
    except serial.SerialTimeoutException as e:
      logging.error("Write timeout on serial port")
    except serial.SerialException as e:
      logging.error("Write exception serial port")
    finally:
      py_serial.flushInput()                                             # Workaround: free write buffer (otherwise the Arduino board hangs)
    THR_LOCK.release()
	
def udp_write(msg):
    bytes = udp_socket.sendto(msg, (udp_ip, udp_port))

def udp_to_ser():                                                       # UDP to serial thread
    global connection
    while py_serial is not None:
        if not py_serial.writable():
            continue

        try:
            udp_data, udp_client = udp_socket.recvfrom(512)             # receive data on UDP
##            if udp_data is not None and connection is False:
##                connection = True
        except socket.timeout:
            logging.error("Write timeout on socket")
        except:
            pass
        else:
            ser_write(udp_data) # write data to serial
            #print "send serial"
        time.sleep(0.001)
			
def ser_to_udp():														# Serial to UDP thread
    while py_serial is not None:
        if not py_serial.readable() or not py_serial.inWaiting() > 0:
            continue
        msg = bytearray()
        msg.append(0)
        payload_length = bytearray()
        payload_length.append(0)
        try:
            THR_LOCK.acquire()
            msg[0] = py_serial.read(1)
            if msg[0] == 254:
                payload_length[0] = py_serial.read()
                msg.append(payload_length[0])
                payload = py_serial.read(payload_length[0] + 6)
                
                for x in payload:
                    msg.append(x)
        except serial.SerialTimeoutException as e:
            logging.error("Read timeout on serial port")
        except serial.SerialException as e:
            logging.error("Read exception on serial port")
        else:
            udp_write(msg)
            #print "send udp"
            #udp_write(ser_msg  # write to UDP
        finally:
            THR_LOCK.release()
        time.sleep(0.001)

def connect_udp():
        global connection
        while connection is False:
                udp_socket.sendto('hello', (udp_ip, udp_port))
                time.sleep(1)
        print "cnct thread done"

def main():
        cnct = threading.Thread(target=connect_udp)
	udptoser=threading.Thread(target=udp_to_ser)
	sertoudp=threading.Thread(target=ser_to_udp)
	cnct.start()
	udptoser.start()
	sertoudp.start()
	
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
