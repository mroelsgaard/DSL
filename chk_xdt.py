import Spectra
import sys
import os
#import string
import time, math

#import numpy as np

import PyTango

def gett():
    timestr=(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    return timestr


fid1=open('xdt_log.dat',"a")
#print(len(sys.argv[0]))
if((len(sys.argv) > 0) and (len(sys.argv[0]))):
    comm=sys.argv[0]
    print('%s XDT %s'%(gett(),comm))
    fid1.write('%s XDT %s\n'%(gett(),comm))



#fid4=open('poslog.dat',"a")
#fid3.write("\n\n-------------------------New run\n")
devs=[]
devs.append(PyTango.DeviceProxy("tango://haspp07eh2:10000/p07/motor/eh2.58"))
#devs.append(PyTango.DeviceProxy("tango://haspp07eh2:10000/p07/motor/eh2.53"))
#devs.append(PyTango.DeviceProxy("tango://haspp07eh2:10000/p07/motor/eh2.56"))
#devs.append(PyTango.DeviceProxy("tango://haspp07eh2:10000/p07/motor/eh2.54"))


whilecond=1
cnt=0
while(whilecond):
    #print(gett())
    if((devs[0].state() == PyTango.DevState.ON)):
        print('%s XDT motor is ON'%(gett()))
        fid1.write('%s XDT motor is ON\n'%(gett()))
        whilecond=0
    else:
        print('%s XDT motor is NOT ON'%(gett()))
        #fid1.write('%s ZDT at least one motor is NOT ON\n'%(gett()))

        cnt=cnt+1
        fid1.write("%s"%(gett()))

        for dev in devs:
    #print(dev.read_attribute("State"))
    #print(devs[0])

            if((dev.state() != PyTango.DevState.ON)):
                print("%s XDT %s is NOT ON"%(gett(),dev))
                fid1.write(" XDT %s is NOT ON "%(dev))
        fid1.write("\n")
        time.sleep(0.1)
    #print(dev.state())

fid1.close()
