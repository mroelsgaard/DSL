#!/usr/bin/env python
"""

####

#
#
# Martin R 28.07.2021
# updated to run in python3
# changed to byte from str on sock.sendall
#

##
this scripts reads data from a SP2000TR and writes them to the
attributes of a VcExecutor
DynamicAttributes (Property)
  pos_ch1,double,rw
  pos_ch2,double,rw
  pos_ch3,double,rw
  sig_ch1,double,rw
  sig_ch2,double,rw
  sig_ch3,double,rw
"""
import socket, select, PyTango, time, sys

DEVICE = "p07/vcexecutor/sp2000tr"
HOST = "hasep211varex01"
PORT = 35320

def main():

    proxy = PyTango.DeviceProxy( DEVICE)

    sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM)

    server_address = ( HOST, PORT)
    sock.settimeout( 3)
    try:
        sock.connect(server_address)
    except Exception as e:
        print( "SP200TRScritp: failed to connect to %s, %s " % ( HOST, PORT))
        return

    sock.sendall(b"\n")
    time.sleep(0.5)
    sock.sendall(b"SetToZero\n")
    if(0):
        sock.sendall(b"IfmSetAGC 0 1\n")
        sock.sendall(b"IfmSetAGC 1 1\n")
        sock.sendall(b"IfmSetAGC 2 1\n")
    #sock.sendall("IfmSetRefMirrorVibration 0 0\n")
    #sock.sendall("%s\n\n"%INPUT)


    time.sleep(.5)
    sock.close()

    return

def gainStart():
     proxy = PyTango.DeviceProxy( DEVICE)

     sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM)

     server_address = ( HOST, PORT)
     sock.settimeout( 3)
     try:
         sock.connect(server_address)
     except Exception as e:
         print( "SP200TRScritp: failed to connect to %s, %s " % ( HOST, PORT))
         return

     sock.sendall( b"\n")
     time.sleep(0.5)
     #sock.sendall( b"SetToZero\n")
     if(1):
         #sock.sendall( b"IfmSetRefMirrorVibration 0 1\n")
         #sock.sendall( b"IfmSetRefMirrorVibration 1 1\n")
         #sock.sendall( b"IfmSetRefMirrorVibration 2 1\n")
         sock.sendall( b"IfmSetAGC 0 1\n")
         sock.sendall( b"IfmSetAGC 1 1\n")
         sock.sendall( b"IfmSetAGC 2 1\n")

     #sock.sendall( b"IfmSetRefMirrorVibration 0 0\n")
     #sock.sendall( b"%s\n\n"%INPUT)


     time.sleep(.5)
     sock.close()

     return
def gainStop():
     proxy = PyTango.DeviceProxy( DEVICE)

     sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM)

     server_address = ( HOST, PORT)
     sock.settimeout( 3)
     try:
         sock.connect(server_address)
     except Exception as e:
         print( "SP200TRScritp: failed to connect to %s, %s " % ( HOST, PORT))
         return

     sock.sendall( b"\n")
     time.sleep(0.5)
     #sock.sendall( b"SetToZero\n")
     if(1):
         #sock.sendall( b"IfmSetRefMirrorVibration 0 1\n")
         #sock.sendall( b"IfmSetRefMirrorVibration 1 1\n")
         #sock.sendall( b"IfmSetRefMirrorVibration 2 1\n")
         sock.sendall( b"IfmSetAGC 0 0\n")
         sock.sendall( b"IfmSetAGC 1 0\n")
         sock.sendall( b"IfmSetAGC 2 0\n")

     #sock.sendall( b"IfmSetRefMirrorVibration 0 0\n")
     #sock.sendall( b"%s\n\n"%INPUT)


     time.sleep(.5)
     sock.close()



if __name__ == "__main__":
    main()
    #gainStart()
