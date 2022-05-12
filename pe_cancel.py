#!/bin/env python


import PyTango
import os
import datetime
import time, sys
import math

current_milli_time = lambda: int(round(time.time() * 1000))


dev_perkctrl  = PyTango.DeviceProxy("tango://haspp07eh2:10000/p07/varexctrl/01")
antwort=dev_perkctrl.command_inout("WriteReadSocket","acquireCancel()")
#dev_out=PyTango.DeviceProxy( "//haspp07eh2:10000/p07/register/eh2.out14")
#dev_out.write_attribute( "Value", 0)


