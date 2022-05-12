import PyTango
devgpib  = PyTango.DeviceProxy("tango://haspp07eh2:10000/p07/gpib/eh2a.09")
dev_det  = PyTango.DeviceProxy("tango://haspp07eh2:10000/p07/varexctrl/01")
import sys
import time

try:
    while True:
        temp = float(devgpib.command_inout("GPIBWriteRead","CRDG?C"))
        filename   = dev_det.command_inout("WriteReadSocket","%s"%("acquisition.filePattern")) 
        patternout = 'ptcalib_annealed_newheater_{}C'.format(temp)
        print(temp)
        time.sleep(5) 
        print(filename)
except KeyboardInterrupt:
    sys.exit()
