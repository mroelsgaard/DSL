import sys
from time import *
from PyTango import *
import os
import datetime
import Spectra
#devperkin  = DeviceProxy("tango://haspp07eh2:10000/p07/pedetector_old/01")
#devperkctrl  = DeviceProxy("tango://haspp07eh2:10000/p07/pectrl_old/01")
devperkin  = DeviceProxy("tango://haspp07eh2:10000/p07/varexdetector/01")
devperkctrl  = DeviceProxy("tango://haspp07eh2:10000/p07/varexctrl/01")

antwort=devperkctrl.command_inout("WriteReadSocket","%s"%("acquisition.fileIndex"))
print(antwort)