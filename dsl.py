#!/usr/bin/python3
#
# ===================================
# P07  Interferometer
#
# Updated 28.07.2021 Martin Roelsgaard
#
#
#
# ===================================
import PyTango
import sys
import numpy as np
import math # atan
import time

# import functions from sios to zero positions
import sios

# import functions from freq generator to start/stop loudspeaker
import frequency_generator

class dsl:
    def __init__(self):
        self.feedbackOn = False
        self.moveMotors = True # for debugging
        self.writeLog   = False # for debugging

        self.loudspeakerOn = False
        self.printDetector = True

        self.thresholdAngle = 0.0005 # degree
        self.thresholdHeight = 0.0001 # mm
        self.thresholdStop = 1
        self.waittime = 0.1 # looptime

        self.chis = 0
        self.phis = 0
        self.zs   = 0
        self.ys   = 0
        self.xs   = 0
        self.mus  = 0
        self.omes = 0

        self.readouts = 1 # no. of readouts per position
        self.p1   = 0
        self.p2   = 0
        self.p3   = 0
        self.a1   = 0
        self.a2   = 0
        self.petra = 0
        self.avgHeight = 0
        self.temp = 0
        self.tempSetpoint = 0
        self.tempD = 0
        self.tempSetpoint = 0
        self.fidx = 0
        self.lastLoopTime = time.localtime()

        # we want to wait inbetween each lakeshore-query to 
        # make it possible to press a button or two on it
        # so we store a time value, and update this by time.time()
        # every time the lakeshore is queried
        self.last_lks_time_wait = 3 # seconds between checks
        self.last_lks_time = time.time()-self.last_lks_time_wait # make sure first round is updated

        self.thresholdHeightMovemany = 10 # "many movements" limit
        self.thresholdAngleMovemany = 9 # "many movements" limit

        # set a string+local logstamp for standalone
        self.logStampStr          = "%Y%m%d_%H%M"
        self.logStamp             = time.strftime(self.logStampStr, time.localtime()) 

        self.init_tango()
        # start values
        self.updateValues()
        #self.chisStart = self.getChis()
        #self.phisStart = self.getPhis()
        #self.zsStart = self.getZs()

    def init_tango(self):
        self.devOmes = PyTango.DeviceProxy("tango://haspp07eh2:10000/p07/motor/eh2.35")
        self.devXs = PyTango.DeviceProxy("tango://haspp07eh2:10000/p07/motor/eh2.40")
        self.devYs = PyTango.DeviceProxy("tango://haspp07eh2:10000/p07/motor/eh2.39")
        self.dev_zs = PyTango.DeviceProxy("tango://haspp07eh2:10000/p07/motor/eh2.38")
        #self.dev_chis = PyTango.DeviceProxy("tango://haspp07eh2:10000/p07/motor/eh2.37") ch37 defect, changed to 77 on eh2b, Olof 02.08.2021
        self.dev_chis = PyTango.DeviceProxy("tango://haspp07eh2b:10000/p07/motor/eh2.77")
        self.dev_phis = PyTango.DeviceProxy("tango://haspp07eh2b:10000/p07/motor/eh2.76")
        self.devMus = PyTango.DeviceProxy("tango://haspp07eh2:10000/p07/vmotor/mus")

        # fixed values to reenable after feedback
        self.dev_zsDefaultbacklash =   0.020          #self.dev_zs.read_attribute('UnitBacklash')
        self.dev_chisDefaultbacklash = 0.0005          #self.dev_chiss.read_attribute('UnitBacklash')
        self.dev_phisDefaultbacklash = 0.0005          #self.dev_phis.read_attribute('UnitBacklash')

        # interferometer devices
        # ch1-3 are legacy, can read from virtualcounter now
        self.dev_ch1  = PyTango.DeviceProxy("tango://haspp07eh2b:10000/p07/motor/eh2.17")
        self.dev_ch2  = PyTango.DeviceProxy("tango://haspp07eh2b:10000/p07/motor/eh2.18")
        self.dev_ch3  = PyTango.DeviceProxy("tango://haspp07eh2b:10000/p07/motor/eh2.21")
        self.dev_vc  = PyTango.DeviceProxy("tango://haspp07eh2:10000/p07/vcexecutor/sp2000tr")

        # detector
        self.dev_det  = PyTango.DeviceProxy("tango://haspp07eh2:10000/p07/varexctrl/01")

        # lakeshore
        self.devgpib  = PyTango.DeviceProxy("tango://haspp07eh2:10000/p07/gpib/eh2a.09")

        # globals
        self.devGlobals  = PyTango.DeviceProxy("tango://haspp07eh2:10000/petra/globals/keyword")

    """
     read functions
    """
    def get_positions(self):
        """
          reads out positions from interferometer
          no return value
        """
        p1, p2, p3 = [0,0,0]

        # readout self.readouts times if averaging is used
        for i in np.arange(0, self.readouts):
            p1 += self.dev_vc.read_attribute("pos_ch1").value
            p2 += self.dev_vc.read_attribute("pos_ch2").value
            p3 += self.dev_vc.read_attribute("pos_ch3").value
        
        # average out
        self.p1 = p1/self.readouts
        self.p2 = p2/self.readouts
        self.p3 = p3/self.readouts
        return
        
    def getChis(self):
        self.chis = self.dev_chis.read_attribute('Position').value
        return self.chis

    def getPhis(self):
        self.phis = self.dev_phis.read_attribute('Position').value
        return self.phis
    
    def getZs(self):
        self.zs = self.dev_zs.read_attribute('Position').value
        return self.zs

    def getYs(self):
        self.ys = self.devYs.read_attribute('Position').value
        return self.ys
   
    def getXs(self):
        self.xs = self.devXs.read_attribute('Position').value
        return self.xs

    def getMus(self):
        self.mus = self.devMus.read_attribute('Position').value
        return self.mus

    def getTemp(self):
        try:
            self.temp = float(self.devgpib.command_inout("GPIBWriteRead","CRDG?C"))
        except:
            self.temp = -10
        return self.temp

    def getTempD(self): 
        try:
            #self.tempD=-9
            self.tempD = float(self.devgpib.command_inout("GPIBWriteRead","CRDG?D"))
        except:
            self.tempD = -10
        return self.tempD

    def getSetpoint(self):
        try:
            self.tempSetpoint = float(self.devgpib.command_inout("GPIBWriteRead","SETP?3"))
        except:
            self.tempSetpoint = -10
        return self.tempSetpoint

    def getFidx(self):
        # read the frame number from detector
        try:
            self.fidx   = self.dev_det.command_inout("WriteReadSocket","%s"%("acquisition.fileIndex")) 
        except:
            self.fidx   = -2
            #self.pr2('Problem reading detector fidx')
    """
     set (move) functions
    """
    def setChis(self, relative_pos):
        # set a relative position to chis motor
        currAngle = self.getChis()
    
        try:
            if self.moveMotors:
                self.dev_chis.write_attribute('Position', currAngle+relative_pos)
        except:
            self.pr2('Motor chis error.')
        return

    def setPhis(self, relative_pos):
        # set a relative position to phis motor
        currAngle = self.getPhis() 
    
        try:
            if self.moveMotors:
                pass
                self.dev_phis.write_attribute('Position', currAngle+relative_pos)
        except:
            self.pr2('Motor phis error.')

    def setZs(self, relative_pos):
        # set relative position on zs motor
        self.getZs()
        currPosition = self.zs
    
        try:
            if self.moveMotors:
                self.dev_zs.write_attribute('Position', currPosition+relative_pos)
        except:
            self.pr2('Motor error zs.')

    # Math functions
    def getAngle(self, p1, p2, dist=3.925):
        # Calculates the angle between two points
        # returns in degrees
        # dist in mm
        angle = 180.0/np.pi*math.atan((p1-p2)/dist)
        return angle

    def get_avg_height(self):
        # calculate the average height from all 3 positions
        self.avgHeight = (self.p1+self.p2+self.p3)/3.0

    def get_beamcurrent(self):
        self.petra = self.devGlobals.read_attribute("BeamCurrent").value 
        return self.petra

    def getOmes(self):
        self.omes = self.devOmes.read_attribute('Position').value
        return self.omes
        
    # feedback functions
    def updateValues(self):
        # goes through and updates all values
        self.getChis()
        self.getPhis()
        self.getXs()
        self.getYs()
        self.getZs()
        self.getMus()
        self.getOmes()
        # lake shore values
        t = time.time()
        if t > self.last_lks_time + self.last_lks_time_wait:
            # limit queries to lakeshore for physical
            # button access
            self.getTemp()
            self.getTempD()
            self.getSetpoint()
            self.last_lks_time = t

        self.get_positions()
        self.get_avg_height()
        # calc angles
        self.a1 = self.getAngle(self.p1, self.p2)
        self.a2 = self.getAngle(self.p2, self.p3)
        # detector
        self.getFidx()
        # beamcurrent
        self.get_beamcurrent()

    def feedbackHeight(self):
        # calculate the average of p1, p2, p3 positions
        # and check against the threshold
        self.get_avg_height()

        # check if height is OK
        if (abs(self.avgHeight) > self.thresholdHeight):
            self.pr2('Height needs adjustments!!')

            if self.feedbackOn:
                # move!
                if (abs(self.avgHeight) > self.thresholdHeightMovemany*self.thresholdHeight):
                    # limit the travel the the threshold if the offset
                    # is very large
                    travel = abs(self.avgHeight)/self.avgHeight*self.thresholdHeight
                else:
                    travel = self.avgHeight
                self.setZs(-travel)

    def feedback_angles(self):
        # 06.08.2020
        # omes is -90 in this config
        # 29.07.2021
        # we are now checking for what omes is. This could be used
        # TODO: to multiply a factor on travel for phis below
        # -1 for 90 and +1 for -90 (as it is configured for right now)
        # a1 - phis
        if (abs(self.a1) > self.thresholdAngle):
            self.pr2('Move phis!!')
            if self.feedbackOn:
                if (abs(self.a1) > self.thresholdAngleMovemany*self.thresholdAngle):
                    # limit the travel to the threshold if the offset
                    # is very large
                    travel = abs(self.a1)/self.a1*self.thresholdAngle
                else:
                    travel = self.a1
                self.setPhis(travel)

        # a2 - chis but in reverse
        if (abs(self.a2) > self.thresholdAngle):
            self.pr2('Move chis!!')
            if self.feedbackOn:
                if (abs(self.a2) > self.thresholdAngleMovemany*self.thresholdAngle):
                    # limit the travel to the threshold if the offset
                    # is very large
                    # it can't be 0 due to if statement above
                    travel = abs(self.a2)/self.a2*self.thresholdAngle
                else:
                    travel = self.a2
                self.setChis(-travel)

    def feedback_loop(self):
        # run through one loop
        self.updateValues()
        self.prLoop() # print all info's to file
        self.lastLoopTime = time.localtime()

        if self.feedbackOn:
            """
             check for the height & angles
             the active movements happen in these functions (if needed)
            """
            self.feedbackHeight()
            self.feedback_angles()

        # wait for the feedback loop time
        time.sleep(self.waittime)

        return

    def check_omes(self):
        """
         returns True if omes = -90
        """
        omesPosition = self.getOmes()

        # is omes within 1 degree of -90?
        res = math.isclose(-90, omesPosition, abs_tol=1)

        return res

    def set_backlast(self, state):
        """
         enable/disable the backlash on the feedback motors
         input = True/False
        """
        if state == True:
            zstate = self.dev_zsDefaultbacklash
            chistate = self.dev_chisDefaultbacklash
            phistate = self.dev_phisDefaultbacklash
        else:
            zstate = 0
            chistate = 0
            phistate = 0

        while self.dev_zs.state() == PyTango.DevState.MOVING:
            # wait a little bit, go again
            time.sleep(0.25)
        self.dev_zs.write_attribute('UnitBacklash', zstate)


        while self.dev_chis.state() == PyTango.DevState.MOVING:
            # wait a little bit, go again
            time.sleep(0.25)
        self.dev_chis.write_attribute('UnitBacklash', chistate)

        while self.dev_phis.state() == PyTango.DevState.MOVING:
            # wait a little bit, go again
            time.sleep(0.25)
        self.dev_phis.write_attribute('UnitBacklash', phistate)

        
    def zero(self):
        """
         use external sios.py script to zero the device
         slow method, will 'hang up' the DSL loop while executing
        """
        sios.main()

    def loudspeaker(self, value):
        """
         loudspeaker module to make mechanical vibrations on the
         setup
        """    
        if value:
            frequency_generator.main('on')
        else:
            frequency_generator.main('off')

    def dsl_gain_start(self):
        sios.gain_start()
    def dsl_gain_stop(self):
        sios.gain_stop()

    def perform_gain_correction(self):
        """
         runs gain correction on the laser interferometer
        """
        self.pr2('Gain correction started!')
        sios.gain_start()
        # wait for some time, and stop it again
        time.sleep(5)
        sios.gain_stop()
        self.pr2('Gain correction finished')

    # log functions
    def pr(self,txt):
        # print to file name hardcoded here
        # prints to file in append mode

        # output location
        logstring         = 'log/log'

        if self.writeLog:
            # writeLog can be True/False for debugging (and can now also be set from gui.py)
            with open('{}_{}.dat'.format(logstring, self.logStamp), 'a') as fid:
                fid.write(txt+'\n')

        #print(txt) # usually this is not printed but instead pr2 with indicators of the 
                    # printed values

    def pr2(self,txt):
        # print to screen + log "FULL" to file name hardcoded here
        # prints to file in append mode
        logstring         = 'log/log'
        if self.writeLog: 
            with open('{}FULL_{}.dat'.format(logstring, self.logStamp), 'a') as fid:
                pass
                fid.write(txt+'\n')
        print(txt)   # screenprint normally on

    def prLoop(self):
        # read all values and put them in file.
        # print both a file with only numbers
        # and to screen + full log including
        # motor movements
        formattedTime = time.strftime("%d%m-%H:%M:%S", self.lastLoopTime)
        self.pr2('{}\t'.format(formattedTime)+
             'p1:{:+.6f}\t'.format(self.p1)+
             'p2:{:+.6f}\t'.format(self.p2)+
             'p3:{:+.6f}\t'.format(self.p3)+
             'T:{:+.1f}\t'.format(self.temp)+
             'Tset:{:+.1f}\t'.format(self.tempSetpoint)+
             'Td:{:+.1f}\t'.format(self.tempD)+
             'a1:{:+.4f}\t'.format(self.a1)+
             'a2:{:+.4f}\t'.format(self.a2)+
             'chis:{:+.4f}\t'.format(self.chis)+
             'phis:{:+.4f}\t'.format(self.phis)+
             #'xs:{:+.5f}\t'.format(self.xs)+          # it is in the GUI too, so most of the time
             #'ys:{:+.5f}\t'.format(self.ys)+          # we don't need this printed to screen
             'zs:{:+.5f}\t'.format(self.zs)+
             #'Rchis:{:+.4f}\t'.format(Rchis)+
             #'Rphis:{:+.4f}\t'.format(Rphis)+
             #'Rzs:{:+.5f}\t'.format(Rzs)+
             'fid:{}\t'.format(self.fidx)
            )
        self.pr('{}\t'.format(formattedTime)+
             '{:+.6f}\t'.format(self.p1)+
             '{:+.6f}\t'.format(self.p2)+
             '{:+.6f}\t'.format(self.p3)+
             '{:+.1f}\t'.format(self.temp)+
             '{:+.1f}\t'.format(self.tempSetpoint)+
             '{:+.1f}\t'.format(self.tempD)+
             '{:+.5f}\t'.format(self.a1)+
             '{:+.5f}\t'.format(self.a2)+
             '{:+.5f}\t'.format(self.chis)+
             '{:+.5f}\t'.format(self.phis)+
             '{:+.5f}\t'.format(self.xs)+
             '{:+.5f}\t'.format(self.ys)+
             '{:+.5f}\t'.format(self.zs)+
             '{:+.7f}\t'.format(self.mus)+
             #'{:+.5f}\t'.format(Rchis)+
             #'{:+.5f}\t'.format(Rphis)+
             #'{:+.5f}\t'.format(Rzs)+
             '{}'.format(self.fidx)
            )
        self.prDetector()

    def prDetector(self):
        if not self.printDetector:
            # if set to False in beginning, this is stopped
            return
        # keeping this if needed later
        try:
            antwort=self.dev_det.WriteReadSocket( "acquisition.userComment1=\"%.2f\""%self.temp )
            antwort=self.dev_det.WriteReadSocket( "acquisition.userComment2=\"p1=%.5f p2=%.5f p3=%.5f\""%(self.p1,self.p2,self.p3) )
            antwort=self.dev_det.WriteReadSocket( "acquisition.userComment3=\"a1=%.5f a2=%.5f z=%.5f\""%(self.a1,self.a2,((self.p1+self.p2+self.p3)/3.0)) )
            #antwort=dev_det.WriteReadSocket( "acquisition.userComment4=\"Rchis=%.5f Rphis=%.5f Rzs=%.5f\""%(Rchis,Rphis,Rzs) )
        except:
            print('detector error')
            pass


if __name__ == '__main__':
    """
     runs in stand-alone CLI mode as well
    """
    dsl = dsl()

    if dsl.check_omes:
        pass
    else:
        print('Omes not -90!!')
        sys.exit()


    dsl.last_lks_time_wait = 0.5 # seconds between temperature checks

    while True:
        # this is the feedback loop for CLI mode
        try:
            dsl.feedback_loop()
            
        except KeyboardInterrupt:
            print('Keyboard interrupt. End!')
            sys.exit()
