#!/usr/bin/python3
#
# ===================================
# P07  Interferometer GUI
#
# Updated 28.07.2021 Martin Roelsgaard
#
# Uses dsl class to control interferometer
# in a PyQT GUI
#
# Note pyqtgraph is an old version
#
#
# ===================================
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QColor, QPalette
from pyqtgraph import PlotWidget, mkPen
from pyqtgraph import ViewBox, PlotCurveItem #for linked 2nd y-axis


import numpy as np
import sys
import time
from dsl import *
from PyTango import DevState

class dsl_gui(QtWidgets.QMainWindow):
    # signal for communicating signals with dsl class
    # currently not in use!
    stop_signal = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(dsl_gui, self).__init__(*args, **kwargs)


        # define some hopefully self-explanatory variables
        self.plotLimit = 750 # for limiting the most recent plots
        self.plotLimitState = True # limit to the most recent self.plotLimit


        # a lot of PyQT GUI follows..
        self.vGrid = QtWidgets.QVBoxLayout()
        self.topLayout = QtWidgets.QHBoxLayout()
        self.bottomLayout = QtWidgets.QHBoxLayout()
        self.graphWidget = PlotWidget()

        
        # styles are kept here
        # labels are not bordered
        self.QLineEditW = 180
        self.styleRed ="""
            QLineEdit {
                background-color: red;
                font-size: 16pt;
            }"""
        self.styleYellow ="""
            QLineEdit {
                background-color: yellow;
                font-size: 16pt;
            }"""
        self.styleBox ="""
            QWidget {
                border-radius: 1px;
                background-color: rgb(210, 210, 210);
                border: 1px solid black;
                }
            QLabel {
                border: 0px;
                font-size: 16pt;
            }
            """
        self.styleMainWindow ="""
            QPushButton {
                font-size: 16pt;
            }
            """
        self.styleLineReadonly ="""
            QLineEdit {
                background-color: rgb(255, 255, 255);
                font-size: 16pt;
                }
            """
        self.styleLineedit ="""
            QLineEdit {
                background-color: rgb(255, 255, 255);
                font-size: 16pt;
                }
            """
        # titles/headers are bold
        self.styleLabelHeader ="""
            QLabel {
                border: 0px;
                font-size: 20pt;
                font: bold;
            }
            """

        # add legend to plot
        self.legend = self.graphWidget.addLegend()
        # ! haspp07eh2 is using an old version of pyqtgraph
        # doing this manually !
        self.legend.layout.setHorizontalSpacing(30)
        #self.legend.horSpacing = 100
        w = 3 # linewidths

        # add the plots
        self.lineP1 = self.graphWidget.plot([], [], 
                                            name='Position 1', 
                                            pen=mkPen(color=(0,0,0),width=w), 
                                            #pen=mkPen(color=(102,0,0),width=w), 
                                            symbol='o', 
                                            symbolSize=0)
        self.lineP2 = self.graphWidget.plot([], [], 
                                            name='Position 2', 
                                            pen=mkPen(color=(102,0,0),width=w))
        self.lineP3 = self.graphWidget.plot([], [], 
                                            name='Position 3', 
                                            pen=mkPen(color=(51,0,25),width=w))
                                            #pen=mkPen(color=(102,0,25),width=w))

        # second yaxis
        self.rightGraphBox = ViewBox()
        self.graphWidget.showAxis('right')
        self.graphWidget.getAxis('right').setLabel('Angles (mdeg.)')
        self.graphWidget.getAxis('right').setPen(mkPen(color=(0,114,178)))
        self.graphWidget.scene().addItem(self.rightGraphBox)
        self.graphWidget.getAxis('right').linkToView(self.rightGraphBox)
        # link X-axis
        self.rightGraphBox.setXLink(self.graphWidget)

    
        self.lineA1 = PlotCurveItem([], [], 
                                            name='Angle 1-2', 
                                            pen=mkPen(color=(0,158,115),width=w))
        self.lineA2 = PlotCurveItem([], [], 
                                            name='Angle 2-3', 
                                            pen=mkPen(color=(0,114,178),width=w))
        self.rightGraphBox.addItem(self.lineA1)
        self.rightGraphBox.addItem(self.lineA2)

        # every time graphWidget is updated, call updateRightAxis():
        self.graphWidget.plotItem.vb.sigResized.connect(self.updateRightAxis)

        # replace tickStrings by custom functions:
        self.graphWidget.getAxis('left').tickStrings = self.tickStrings
        self.graphWidget.getAxis('right').tickStrings = self.tickStrings

        # styling
        self.graphWidget.setTitle('Position/angle time-series')
        self.graphWidget.setBackground('w')
        styles = {'color':'k', 'font-size': 28}
        self.graphWidget.setLabel('left', 'Position (um)',**styles)
        self.graphWidget.getAxis('left').setPen(mkPen(color=(142,0,0)))
        self.graphWidget.setLabel('bottom', 'Time (seconds)', **styles)
        for ax in ['bottom', 'top']:
            self.graphWidget.getAxis(ax).setPen('k')
            self.graphWidget.showAxis(ax)

        
        # setup the top layout and connect
        # button zeroing
        self.btnZero = QtWidgets.QPushButton()
        self.btnZero.setText('Zero positions')
        self.btnZero.clicked.connect(self.zeroPositions)
        self.topLayout.addWidget(self.btnZero)

        # button run
        self.btnRun = QtWidgets.QPushButton()
        self.btnRun.setText('Feedback start')
        self.btnRun.clicked.connect(self.startStop)
        self.btnRun.setStyleSheet("background-color: red")
        self.topLayout.addWidget(self.btnRun)

        # button clear
        self.btnClear = QtWidgets.QPushButton()
        self.btnClear.setText('Reset plot')
        self.btnClear.clicked.connect(self.clearPlot)
        self.topLayout.addWidget(self.btnClear)

        # button set new settings
        self.btnNewThreshold = QtWidgets.QPushButton()
        self.btnNewThreshold.setText('Set new thresholds')
        self.btnNewThreshold.clicked.connect(self.setNewThres)
        self.topLayout.addWidget(self.btnNewThreshold)

        # button loudspeaker
        self.btnLoudspeaker = QtWidgets.QPushButton()
        self.btnLoudspeaker.setText('Loudspeaker OFF')
        self.btnLoudspeaker.clicked.connect(self.freqGenerator)
        #self.topLayout.addWidget(self.btnLoudspeaker)
        
        # button gaincorrection
        self.btnGain = QtWidgets.QPushButton()
        self.btnGain.setText('DSL Gain Correction')
        self.btnGain.clicked.connect(self.performGain)
        self.topLayout.addWidget(self.btnGain)
        # should be inactive to begin with...
        #self.btnGain.setStyleSheet("background-color: grey")
        self.btnGain.setStyleSheet('background-color: red')

        # line 2 in top layout
        # enable/disable running plot limits
        self.topLayout2 = QtWidgets.QHBoxLayout()
        self.topLayoutPlotLimit = QtWidgets.QHBoxLayout()
        self.chkPlotAll = QtWidgets.QCheckBox('Plot limit')
        self.chkPlotAll.stateChanged.connect(self.plotLimitChangeState)
        self.chkPlotAll.setCheckState(self.plotLimitState)
        self.chkPlotAll.setTristate(False)
        self.topLayoutPlotLimit.addWidget(self.chkPlotAll)

        # number lineedit for plot limits
        self.dispPlotLimit = QtWidgets.QLineEdit()
        self.dispPlotLimit.setText(str(self.plotLimit))
        self.dispPlotLimit.setFixedWidth(self.QLineEditW)
        self.topLayoutPlotLimit.addWidget(self.dispPlotLimit)

        # enable/disable feedback-logging
        self.chkWriteLog = QtWidgets.QCheckBox('Write logfiles (auto-en/disables on feedback)')
        self.chkWriteLog.stateChanged.connect(self.writeLogStateChange)
        #self.chkWriteLog.setChecked(self.dsl.writeLog)
        self.chkWriteLog.setTristate(False)
        # a bug in PyQt5 here? I am not sure. User->full check, this script->partially 

        # I define ratios (the numbers) manually + add a stretch to create a whitespace
        self.topLayout2.addLayout(self.topLayoutPlotLimit,1)
        self.topLayout2.addStretch(4)
        self.topLayout2.addWidget(self.chkWriteLog,2)
        
        


        # setup the bottom layout
        # top line = 4 vertical boxes inside a widget (W)
        # positions
        # P1-3 widget
        self.layoutPositionW = QtWidgets.QWidget()
        self.layoutPositionW.setStyleSheet(self.styleBox)
        # P1-3 layout
        self.layoutPositions = QtWidgets.QVBoxLayout(self.layoutPositionW)
        self.layoutPositions.setAlignment(QtCore.Qt.AlignTop)
        self.labelPositions = QtWidgets.QLabel('Interferometer position reads')
        self.labelPositions.setStyleSheet(self.styleLabelHeader)
        self.layoutPositions.addWidget(self.labelPositions)
        # each line for label+lineedit
        self.layoutPositions1 = QtWidgets.QHBoxLayout()
        self.layoutPositions2 = QtWidgets.QHBoxLayout()
        self.layoutPositions3 = QtWidgets.QHBoxLayout()
        self.dispP1 = QtWidgets.QLineEdit()
        self.dispP1.setText('0')
        self.layoutPositions1.addWidget(QtWidgets.QLabel('Position 1'))
        self.layoutPositions1.addWidget(self.dispP1)
        self.dispP2 = QtWidgets.QLineEdit()
        self.dispP2.setText('0')
        self.layoutPositions2.addWidget(QtWidgets.QLabel('Position 2'))
        self.layoutPositions2.addWidget(self.dispP2)
        self.dispP3 = QtWidgets.QLineEdit()
        self.dispP3.setText('0')
        self.layoutPositions3.addWidget(QtWidgets.QLabel('Position 3'))
        self.layoutPositions3.addWidget(self.dispP3)
        # style positions
        for pos in [self.layoutPositions1, self.layoutPositions2, self.layoutPositions3]:
            self.layoutPositions.addLayout(pos)
        # add the widget to bottomLayout
        self.bottomLayout.addWidget(self.layoutPositionW)

        # angles
        self.layoutAnglesW = QtWidgets.QWidget()
        self.layoutAnglesW.setStyleSheet(self.styleBox)
        self.layoutAngles = QtWidgets.QVBoxLayout(self.layoutAnglesW)
        self.labelAngle = QtWidgets.QLabel('Interferometer calculated angles')
        self.labelAngle.setStyleSheet(self.styleLabelHeader)
        self.layoutAngles.addWidget(self.labelAngle)
        self.layoutAngles.setAlignment(QtCore.Qt.AlignTop)
        self.layoutAngles1 = QtWidgets.QHBoxLayout()
        self.layoutAngles2 = QtWidgets.QHBoxLayout()
        # disp+labels
        self.dispA1 = QtWidgets.QLineEdit()
        self.dispA1.setText('0')
        self.layoutAngles1.addWidget(QtWidgets.QLabel('Angle 1 (P1-P2)'))
        self.layoutAngles1.addWidget(self.dispA1)
        self.dispA2 = QtWidgets.QLineEdit()
        self.dispA2.setText('0')
        self.layoutAngles2.addWidget(QtWidgets.QLabel('Angle 2 (P2-P3)'))
        self.layoutAngles2.addWidget(self.dispA2)
        #styling
        for angle in [self.layoutAngles1, self.layoutAngles2]:
            self.layoutAngles.addLayout(angle)
        self.bottomLayout.addWidget(self.layoutAnglesW) 

        # motors
        # in widget with vertical box with label+lineedit in horizontal box
        self.layoutMotorsW = QtWidgets.QWidget()
        self.layoutMotorsW.setStyleSheet(self.styleBox)
        self.layoutMotors = QtWidgets.QVBoxLayout(self.layoutMotorsW)
        self.layoutMotors.setAlignment(QtCore.Qt.AlignTop)
        self.labelMotors = QtWidgets.QLabel('Motor positions')
        self.labelMotors.setStyleSheet(self.styleLabelHeader)
        self.layoutMotors.addWidget(self.labelMotors)
        self.layoutMotorsChis = QtWidgets.QHBoxLayout()
        self.layoutMotorsPhis = QtWidgets.QHBoxLayout()
        self.layoutMotorsXs = QtWidgets.QHBoxLayout()
        self.layoutMotorsYs = QtWidgets.QHBoxLayout()
        self.layoutMotorsZs = QtWidgets.QHBoxLayout()
        self.layoutMotorsMus = QtWidgets.QHBoxLayout()
        self.layoutMotorsOmes = QtWidgets.QHBoxLayout()
        #displays
        self.dispPhis = QtWidgets.QLineEdit()
        self.dispPhis.setText('0')
        self.layoutMotorsPhis.addWidget(QtWidgets.QLabel('phis'))
        self.layoutMotorsPhis.addWidget(self.dispPhis)
        self.dispChis = QtWidgets.QLineEdit()
        self.dispChis.setText('0')
        self.layoutMotorsChis.addWidget(QtWidgets.QLabel('chis'))
        self.layoutMotorsChis.addWidget(self.dispChis)

        self.dispXs = QtWidgets.QLineEdit()
        self.dispXs.setText('0')
        self.layoutMotorsXs.addWidget(QtWidgets.QLabel('xs'))
        self.layoutMotorsXs.addWidget(self.dispXs)

        self.dispYs = QtWidgets.QLineEdit()
        self.dispYs.setText('0')
        self.layoutMotorsYs.addWidget(QtWidgets.QLabel('ys'))
        self.layoutMotorsYs.addWidget(self.dispYs)

        self.dispZs = QtWidgets.QLineEdit()
        self.dispZs.setText('0')
        self.layoutMotorsZs.addWidget(QtWidgets.QLabel('zs'))
        self.layoutMotorsZs.addWidget(self.dispZs)

        self.dispMus = QtWidgets.QLineEdit()
        self.dispMus.setText('INIT')
        self.layoutMotorsMus.addWidget(QtWidgets.QLabel('mus'))
        self.layoutMotorsMus.addWidget(self.dispMus)
        self.dispOmes = QtWidgets.QLineEdit()
        self.dispOmes.setText('INIT')
        self.layoutMotorsOmes.addWidget(QtWidgets.QLabel('omes'))
        self.layoutMotorsOmes.addWidget(self.dispOmes)

        # add to layout in loop
        for mot in [self.layoutMotorsChis, self.layoutMotorsPhis, 
                    self.layoutMotorsXs, self.layoutMotorsYs,
                    self.layoutMotorsZs, self.layoutMotorsMus,
                    self.layoutMotorsOmes]:
            self.layoutMotors.addLayout(mot)
        # add to widget
        self.bottomLayout.addWidget(self.layoutMotorsW)

        
        # infos
        # in widget as above
        self.layoutInfosW = QtWidgets.QWidget()
        self.layoutInfosW.setStyleSheet(self.styleBox)
        self.layoutInfos = QtWidgets.QVBoxLayout(self.layoutInfosW)
        self.layoutInfos.setAlignment(QtCore.Qt.AlignTop)
        self.labelInfos = QtWidgets.QLabel('Infos')
        self.labelInfos.setStyleSheet(self.styleLabelHeader)
        self.layoutInfos.addWidget(self.labelInfos)
        self.layoutInfosPetra = QtWidgets.QHBoxLayout()
        self.layoutInfosTemp = QtWidgets.QHBoxLayout()
        self.layoutInfosTempD = QtWidgets.QHBoxLayout()
        self.layoutInfosTempSetpoint = QtWidgets.QHBoxLayout()

        self.dispTempSetpoint = QtWidgets.QLineEdit()
        self.dispTempSetpoint.setText('0')
        self.layoutInfosTempSetpoint.addWidget(QtWidgets.QLabel('Temperature Setpoint'))
        self.layoutInfosTempSetpoint.addWidget(self.dispTempSetpoint)

        self.dispTemp = QtWidgets.QLineEdit()
        self.dispTemp.setText('0')
        self.layoutInfosTemp.addWidget(QtWidgets.QLabel('Temperature C'))
        self.layoutInfosTemp.addWidget(self.dispTemp)

        self.dispTempD = QtWidgets.QLineEdit()
        self.dispTempD.setText('0')
        self.layoutInfosTempD.addWidget(QtWidgets.QLabel('Temperature D'))
        self.layoutInfosTempD.addWidget(self.dispTempD)

        self.dispPetra = QtWidgets.QLineEdit()
        self.dispPetra.setText('0')
        self.layoutInfosPetra.addWidget(QtWidgets.QLabel('PETRA Beamcurrent'))
        self.layoutInfosPetra.addWidget(self.dispPetra)
        # add to layout
        for info in [self.layoutInfosPetra, self.layoutInfosTempSetpoint, 
                    self.layoutInfosTemp, self.layoutInfosTempD]:
            self.layoutInfos.addLayout(info)
        # add to widget
        self.bottomLayout.addWidget(self.layoutInfosW)

        # setup bottomlayout2 - horizontal line at the bottom
        # otherwise in the same way
        # vertical bottom2V surrounding for title + adding more lines if need be
        self.bottom2W = QtWidgets.QWidget()
        self.bottom2W.setStyleSheet(self.styleBox)
        self.bottom2V = QtWidgets.QVBoxLayout(self.bottom2W) # vertical for multiple lines
        self.labelBottom = QtWidgets.QLabel('Interferometer settings, detector etc.')
        self.labelBottom.setStyleSheet(self.styleLabelHeader)
        self.bottom2V.addWidget(self.labelBottom)
        self.bottom2H = QtWidgets.QHBoxLayout()
        self.bottom2V.addLayout(self.bottom2H) # add 1 H line to that
        self.dispFidx = QtWidgets.QLineEdit()
        self.dispFidx.setText('0')
        self.bottom2H.addWidget(QtWidgets.QLabel('Detector IDX'))
        self.bottom2H.addWidget(self.dispFidx)
        self.dispWaittime = QtWidgets.QLineEdit()
        self.dispWaittime.setText('0')
        self.bottom2H.addWidget(QtWidgets.QLabel('Feedback looptime'))
        self.bottom2H.addWidget(self.dispWaittime)
        self.dispThresholdP = QtWidgets.QLineEdit()
        self.dispThresholdP.setText('0.5')
        self.bottom2H.addWidget(QtWidgets.QLabel('Threshold position'))
        self.bottom2H.addWidget(self.dispThresholdP)
        self.dispThresholdA = QtWidgets.QLineEdit()
        self.dispThresholdA.setText('0')
        self.bottom2H.addWidget(QtWidgets.QLabel('Threshold angle'))
        self.bottom2H.addWidget(self.dispThresholdA)

        # central grid setup
        self.vGrid.addLayout(self.topLayout)
        self.vGrid.addLayout(self.topLayout2)
        self.vGrid.addWidget(self.graphWidget)
        self.vGrid.addLayout(self.bottomLayout)
        self.vGrid.addWidget(self.bottom2W)
        self.mainwidget = QtWidgets.QWidget()
        self.mainwidget.setLayout(self.vGrid)
        self.mainwidget.setStyleSheet(self.styleMainWindow)
        self.setCentralWidget(self.mainwidget)

        # style the QLineEdit to be white background + readonly
        for disp in [self.dispPetra, self.dispTempSetpoint, 
                     self.dispTemp, self.dispTempD, 
                     self.dispFidx, self.dispXs, self.dispYs,
                     self.dispWaittime, self.dispThresholdP, self.dispThresholdA,
                     self.dispP1, self.dispP2, self.dispP3, self.dispA1, self.dispA2,
                     self.dispChis, self.dispZs, self.dispPhis, self.dispMus, self.dispOmes]:
            disp.readOnly = True
            disp.setStyleSheet(self.styleLineReadonly)
            disp.setAlignment(QtCore.Qt.AlignRight)
            disp.setFixedWidth(self.QLineEditW)


        self.start_dsl()

        # only here is it possible to refer to dsl
        self.chkWriteLog.setChecked(self.dsl.writeLog)

    def setColorWhileMoving(self, disp, dev):
        # sets a motor-disp yellow while dev is moving
        if dev.state() == DevState.MOVING:
            c = self.styleYellow
        else:
            c = self.styleLineReadonly
        disp.setStyleSheet(c)

    def updateRightAxis(self):
        """
         re-adjusts the right axis based on a signal
         from graphWidget that it has been re-sized
        """
        self.rightGraphBox.setGeometry(self.graphWidget.plotItem.vb.sceneBoundingRect())
    
    def tickStrings(self, values, scale, spacing):
        """
         pyqtgraph return tickstrings without scientific notation
        """
        return [value*1000 for value in values]

    def updateGui(self):
        """
         runs regularly to update the GUI disp's with
         numbers from the DSL instance
        """
        self.dispP1.setText('{:0.5f} mm'.format(self.dsl.p1))
        self.dispP2.setText('{:0.5f} mm'.format(self.dsl.p2))
        self.dispP3.setText('{:0.5f} mm'.format(self.dsl.p3))

        self.dispChis.setText('{:0.5f}'.format(self.dsl.chis))
        self.dispPhis.setText('{:0.5f}'.format(self.dsl.phis))
        self.dispXs.setText('{:0.5f}'.format(self.dsl.xs))
        self.dispYs.setText('{:0.5f}'.format(self.dsl.ys))
        self.dispZs.setText('{:0.5f}'.format(self.dsl.zs))
        self.dispMus.setText('{:0.7f}'.format(self.dsl.mus))
        self.dispOmes.setText('{:0.2f}'.format(self.dsl.omes))

        self.dispPetra.setText('{:02.1f} mA'.format(self.dsl.petra))
        self.dispTemp.setText('{:02f} C'.format(self.dsl.temp))
        self.dispTempD.setText('{:02f} C'.format(self.dsl.tempD))
        self.dispTempSetpoint.setText('{:02f} C'.format(self.dsl.tempSetpoint))

        self.dispFidx.setText('{}'.format(self.dsl.fidx))
        self.dispWaittime.setText('{:0.3f} s'.format(self.dsl.waittime))
        self.dispThresholdP.setText('{:0.4f} mm'.format(self.dsl.thresholdHeight))
        self.dispThresholdA.setText('{:0.4f} deg.'.format(self.dsl.thresholdAngle))

        # set stylesheets to indicate movements required
        c = self.styleLineReadonly # nothing is to be changed
        if abs(self.dsl.avgHeight) > self.dsl.thresholdHeight:
            c = self.styleYellow
        if abs(self.dsl.avgHeight) > self.dsl.thresholdHeightMovemany*self.dsl.thresholdHeight:
            c = self.styleRed
        for disp in [self.dispP1, self.dispP2, self.dispP3]:
            disp.setStyleSheet(c)

        self.dispA1.setText('{:0.5f} deg.'.format(self.dsl.a1))
        if abs(self.dsl.a1) > self.dsl.thresholdAngle:
            c = self.styleYellow
        if abs(self.dsl.a1) > self.dsl.thresholdAngleMovemany*self.dsl.thresholdAngle:
            c = self.styleRed
        self.dispA1.setStyleSheet(c)

        self.dispA2.setText('{:0.5f} deg.'.format(self.dsl.a2))
        if abs(self.dsl.a2) > self.dsl.thresholdAngle:
            c = self.styleYellow
        if abs(self.dsl.a2) > self.dsl.thresholdAngleMovemany*self.dsl.thresholdAngle:
            c = self.styleRed
        self.dispA2.setStyleSheet(c)

        # check if motor is moving and set disp colors
        self.setColorWhileMoving(self.dispChis, self.dsl.devChis)
        self.setColorWhileMoving(self.dispPhis, self.dsl.devPhis)
        self.setColorWhileMoving(self.dispMus, self.dsl.devMus)
        self.setColorWhileMoving(self.dispOmes, self.dsl.devOmes)
        self.setColorWhileMoving(self.dispXs, self.dsl.devXs)
        self.setColorWhileMoving(self.dispYs, self.dsl.devYs)
        self.setColorWhileMoving(self.dispZs, self.dsl.devZs)
        """
        # comment: keep working code while testing above subroutine
        # change color while moving
        if self.dsl.devChis.state() == DevState.MOVING:
            c = self.styleYellow
        else:
            c = self.styleLineReadonly
        self.dispChis.setStyleSheet(c)
        
        if self.dsl.devPhis.state() == DevState.MOVING:
            c = self.styleYellow
        else:
            c = self.styleLineReadonly
        self.dispPhis.setStyleSheet(c)

        if self.dsl.devZs.state() == DevState.MOVING:
            c = self.styleYellow
        else:
            c = self.styleLineReadonly
        self.dispZs.setStyleSheet(c)
        
        if self.dsl.devMus.state() == DevState.MOVING:
            c = self.styleYellow
        else:
            c = self.styleLineReadonly
        self.dispMus.setStyleSheet(c)
             
        if self.dsl.devOmes.state() == DevState.MOVING:
            c = self.styleYellow
        else:
            c = self.styleLineReadonly
        self.dispOmes.setStyleSheet(c)
        """


        # get some data
        self.dsl.dataP1.append(self.dsl.p1)
        self.dsl.dataP2.append(self.dsl.p2)
        self.dsl.dataP3.append(self.dsl.p3)
        self.dsl.dataA1.append(self.dsl.a1)
        self.dsl.dataA2.append(self.dsl.a2)
        self.dsl.dataTime.append(time.time()-self.dsl.t0)

        if self.dispPlotLimit.isModified():
            if self.dispPlotLimit.text().isnumeric():
                self.plotLimit = int(self.dispPlotLimit.text())
            else:
                print('Plot limit not numeric')
            # reset status anyhow to not re-run before something else is modified
            self.dispPlotLimit.setModified(False)
        self.updatePlot()
        
    def updatePlot(self):
        length = len(self.dsl.dataTime)
        if self.plotLimitState and length > self.plotLimit:
            plotrange = slice(len(self.dsl.dataTime)-self.plotLimit, -1)
        else:
            plotrange = slice(0,-1)
        self.lineP1.setData(self.dsl.dataTime[plotrange], self.dsl.dataP1[plotrange])
        self.lineP2.setData(self.dsl.dataTime[plotrange], self.dsl.dataP2[plotrange])
        self.lineP3.setData(self.dsl.dataTime[plotrange], self.dsl.dataP3[plotrange])
        self.lineA1.setData(self.dsl.dataTime[plotrange], self.dsl.dataA1[plotrange])
        self.lineA2.setData(self.dsl.dataTime[plotrange], self.dsl.dataA2[plotrange])

    def start_dsl(self):
        # create self.dsl object        
        self.dsl = dsl()

        # connect stop signal if desired option (#TODO: I haven't implemented)
        self.stop_signal.connect(self.dsl.stop)

        # use dsl signal implemented in inherited class below
        # to update GUI when loop is updated
        # TODO: if feedbackLoop() runs twice before class gui discovers this,
        # a point will not be plotted. But is the GUI ever slower than 1 round?
        self.dsl.finished.connect(self.updateGui)

        # start the Thread for DSL
        self.dsl.start()


    ####
    #
    # action functions
    #
    ####
    def zeroPositions(self):
        """
         zeroes p1,p2,p3 to this reference point

         uses sios.py as external script, which communicates
         with device directly by python socket.
        """
        self.dsl.pr2('Zeroing') # output to FULL logfile
        self.dsl.zero()

    def performGain(self):
        """
         we decided to add this function that will do everything,
         and remove the second button.
        """

        # TODO: some weird thread-blocking going on here
        # I need to do it in the separate thread...
        # enable loudspeaker
        if self.dsl.loudspeakerOn:
            # already running, return
            return
        self.btnGain.clicked.disconnect()
        self.btnGain.setStyleSheet("background-color: green")

        # will enable loudspeaker
        self.freqGenerator()
        # wait 1 sec before enabling gaincorrection
        #time.sleep(1)
        
        self.dslGain()

        # once the above is finished, disable loudspeaker again
        #time.sleep(1)
        self.freqGenerator()

        # reenable button
        self.btnGain.clicked.connect(self.performGain)
        self.btnGain.setStyleSheet("")

    def performGain(self):
        # temp: I don't understand things, so now just turn on loudspeaker
        # start, and then change function.

        if self.dsl.loudspeakerOn:
            # running, stop it
            self.btnGain.setStyleSheet('background-color: red')
            self.freqGenerator()
            self.dsl.dslGainStop()
        else:
            # not running, start it
            self.btnGain.setStyleSheet('background-color: green')
            self.freqGenerator()
            self.dsl.dslGainStart()

    def dslGain(self):
        """
         performs 1 round of gaincorrection
        """
        
        # go out of function if frequency generator is not on
        if not self.dsl.loudspeakerOn:
            self.dsl.pr2('gain button pressed. Loudspeaker not on, doing nothing')
            return

        self.dsl.performGainCorrection()

    def freqGenerator(self):
        """
         turns frequency generator on or off depending
         on current status

         used for gain correction of laser interferometer
        """
        if self.dsl.loudspeakerOn:
            # on, turn it off
            self.dsl.loudspeakerOn = False
            self.btnLoudspeaker.setText('Loudspeaker OFF')
            self.btnLoudspeaker.setStyleSheet("") # no style = not running
            
            # lock button again
            # disabled at the moment
            #self.btnGain.setStyleSheet("background-color: grey;")
        else:
            # off, turn it on
            self.dsl.loudspeakerOn = True
            self.btnLoudspeaker.setText('Loudspeaker ON')
            self.btnLoudspeaker.setStyleSheet("background-color: green")

            # now it is possible to run gain correction, so turn button OK
            #disabled at the moment
            #self.btnGain.setStyleSheet("")
        
        # here the action happens...
        self.dsl.pr2('LOUDSPEAKER TURNED TO: {}'.format(self.dsl.loudspeakerOn))
        self.dsl.loudspeaker(self.dsl.loudspeakerOn)


    def startStop(self):
        """
         starts and stops the feedback on the fly
        """
        if self.dsl.checkOmes():
            pass
        else:
            print('omes is NOT -90!!!!!!')
            msg = QtWidgets.QMessageBox()
            msg.setText('Oops!')
            msg.setIcon(QtWidgets.QMessageBox.Information)
            msg.setInformativeText('omes is NOT -90. Nothing has been done')
            msg.setWindowTitle('Omes not -90')
            msg.exec_()
            return

        if self.dsl.feedbackOn:
            # feedback ON, turn it off
            self.dsl.pr2('stopping')

            # style run button
            self.btnRun.setStyleSheet("background-color: red")
            self.btnRun.setText('Feedback start')
            self.btnNewThreshold.setStyleSheet("") # show it is clickable

            # disable log writing
            self.chkWriteLog.setChecked(False)

            # stop DSL
            self.dsl.feedbackOn = False

            # turn on backlash
            self.dsl.setBacklash(True)
    
            # set LKS queries back to slow when not running
            self.dsl.lastLKSTimeWait = self.oldLKSWait

        else:
            # feedback OFF, turn it on
            # make new logfile
            self.dsl.logStamp = time.strftime(self.dsl.logStampStr, time.localtime()) 
            self.dsl.pr2('Starting')
            
            # enable log writing
            self.chkWriteLog.setChecked(True)

            # config DSL to be running
            self.dsl.feedbackOn = True

            # set UI
            self.btnRun.setStyleSheet("background-color: green")
            self.btnRun.setText('Feedback stop')
            self.btnNewThreshold.setStyleSheet("background-color: grey")

            # turn off backlash
            self.dsl.setBacklash(False)

            # do fast LKS queries while running (and slow it when disable above)
            self.oldLKSWait = self.dsl.lastLKSTimeWait
            self.dsl.lastLKSTimeWait = 0.2

    def clearPlot(self):
        """
         Clear the GUI plot, including data
         emits a dsl.finished() event and thus
         directly plotting the current values again
        """
        # clear data by re-initializing them
        self.dsl.initData()
        self.dsl.finished.emit()

    def plotLimitChangeState(self):
        # chkPlotLimit has changed > update the variable
        self.plotLimitState = self.chkPlotAll.isChecked()

    def writeLogStateChange(self):
        """
         chkWriteLog has changed - set the external variable
        """
        """
        # change from one to the other
        if self.dsl.writeLog:
            self.dsl.writeLog = True
        else:
            self.dsl.writeLog = False
        """
        self.dsl.writeLog = self.chkWriteLog.isChecked()

    def setNewThres(self):
        """
         setNewThres button pressed. Open a dialog and create
         new settings.
        """
        if self.dsl.feedbackOn:
            # if the feedback is running,
            # do nothing. *button still works, but does nothing
            return

        # open dialog and put a widget inside
        dialog = QtWidgets.QDialog()
        dialogW = QtWidgets.QWidget(dialog)
        
        # dialogV contains all the sub-verticals
        dialogV = QtWidgets.QVBoxLayout(dialogW)
        thresholds = QtWidgets.QVBoxLayout()
        dialogV.addLayout(thresholds)

        # top label
        thresLabel = QtWidgets.QLabel('Thresholds')
        thresLabel.setStyleSheet(self.styleLabelHeader)
        thresholds.addWidget(thresLabel)

        # position threshold
        pos = QtWidgets.QHBoxLayout()
        thresholds.addLayout(pos)
        pos.addWidget(QtWidgets.QLabel("Position threshold [mm]"))
        dispNewPos = QtWidgets.QLineEdit()
        dispNewPos.setText(str(self.dsl.thresholdHeight))
        pos.addWidget(dispNewPos)

        # angle threshold
        ang = QtWidgets.QHBoxLayout()
        thresholds.addLayout(ang)
        ang.addWidget(QtWidgets.QLabel("Angle threshold [deg.]"))
        dispNewAng = QtWidgets.QLineEdit()
        dispNewAng.setText(str(self.dsl.thresholdAngle))
        ang.addWidget(dispNewAng)


        # widget for many-move limits
        MMW = QtWidgets.QWidget()
        MMW.setStyleSheet(self.styleBox)
        MM = QtWidgets.QVBoxLayout(MMW)

        # add it to dialogV
        dialogV.addWidget(MMW)

        # Labels and widgets
        MMLabel = QtWidgets.QLabel('Move-many limits')
        MMLabel.setStyleSheet(self.styleLabelHeader)
        MM.addWidget(MMLabel)
        MM.addWidget(QtWidgets.QLabel('Limits the max. number of moves on the motors'))
        MM.addWidget(QtWidgets.QLabel('The motor will move this no. of times'))
        MM.addWidget(QtWidgets.QLabel('and proceed in the loop'))
        angMM = QtWidgets.QHBoxLayout()
        MM.addLayout(angMM)
        angMMLabel = QtWidgets.QLabel("Angle")
        angMM.addWidget(angMMLabel)
        dispNewAngMM = QtWidgets.QLineEdit()
        dispNewAngMM.setText(str(self.dsl.thresholdAngleMovemany))
        angMM.addWidget(dispNewAngMM)
        posMM = QtWidgets.QHBoxLayout()
        MM.addLayout(posMM)
        posMM.addWidget(QtWidgets.QLabel("Position"))
        dispNewPosMM = QtWidgets.QLineEdit()
        dispNewPosMM.setText(str(self.dsl.thresholdHeightMovemany))
        posMM.addWidget(dispNewPosMM)

        # widget for loop waittime setting
        timeW = QtWidgets.QWidget()
        timeW.setStyleSheet(self.styleBox)
        # make layout and add it to dialog
        timeL = QtWidgets.QVBoxLayout(timeW)
        dialogV.addWidget(timeW)

        # labels and widgets
        timeHeader = QtWidgets.QLabel('Feedback loop time')
        timeHeader.setStyleSheet(self.styleLabelHeader)
        timeL.addWidget(timeHeader)
        timeL.addWidget(QtWidgets.QLabel('Sets the time between loops!'))
        timeLH = QtWidgets.QHBoxLayout()
        timeL.addLayout(timeLH)
        timeLH.addWidget(QtWidgets.QLabel('Loop wait time [sec.]'))
        dispWaittime = QtWidgets.QLineEdit()
        dispWaittime.setText(str(self.dsl.waittime))
        timeLH.addWidget(dispWaittime)
        timeLKSLayout = QtWidgets.QHBoxLayout()
        timeLKSLayout.addWidget(QtWidgets.QLabel('LKS Query wait'))
        dispLKS = QtWidgets.QLineEdit()
        dispLKS.setText(str(self.dsl.lastLKSTimeWait))
        timeLKSLayout.addWidget(dispLKS)    
        timeL.addLayout(timeLKSLayout)


        # style the lineedits
        for disp in [dispWaittime, dispNewPosMM, dispNewAngMM, 
                    dispNewAng, dispNewPos, dispLKS]:
            disp.setStyleSheet(self.styleLineedit)
            disp.setAlignment(QtCore.Qt.AlignRight)
            disp.setFixedWidth(120)

        # buttons layout
        ok  = QtWidgets.QHBoxLayout()
        dialogV.addLayout(ok)
        btnApply = QtWidgets.QPushButton()
        btnApply.setText('Apply')
        ok.addWidget(btnApply)
        btnCancel = QtWidgets.QPushButton()
        btnCancel.setText('Cancel')
        ok.addWidget(btnCancel)

        # size adjustment after all have been created
        dialogW.adjustSize()

        # connect buttons
        btnApply.clicked.connect(lambda: self.updateThreshold(dialog, 
                                                    float(dispNewAng.text()), 
                                                    float(dispNewPos.text()),
                                                    int(dispNewPosMM.text()),
                                                    int(dispNewAngMM.text()),
                                                    float(dispWaittime.text()),
                                                    float(dispLKS.text())))
        btnCancel.clicked.connect(lambda: self.updateThreshold(dialog))
        dialog.setWindowTitle("Enter new threshold values")
        
        # and go! 
        dialog.exec()

    def updateThreshold(self,dialog, thresAng=None, thresPos=None, 
                        posMM=None, angMM=None, wt=None, lks=None):
        """
         # click buttons from setNewThres dialog above
        """
        if thresAng is not None:
            self.dsl.thresholdAngle = thresAng
        if thresPos is not None:
            self.dsl.thresholdHeight = thresPos
        if posMM is not None:
            self.dsl.thresholdHeightMovemany = posMM
        if angMM is not None:
            self.dsl.thresholdAngleMovemany = angMM
        if wt is not None:
            self.dsl.waittime = wt
        if lks is not None:
            self.dsl.lastLKSTimeWait = float(lks)

        dialog.accept()
    

class dsl(QtCore.QThread, dsl):
    """
     inherits DSL for the laserinterferometer and adds signals.
     This also stores the data, rather than in the GUI.
    """
    def __init__(self, parent=None):
        super().__init__() # init as normal dsl

        # inherent the DSL but establish the pyqtSignal
        # to enable emits
        #finished = QtCore.pyqtSignal()

        # continue_run is not used at the moment
        self.continue_run = True # insert loop condition to start/stop thread
        self.initData() # init data lists

    def initData(self):
        """
         init data lists
        """
        self.dataP1 = []
        self.dataP2 = []
        self.dataP3 = []
        self.dataA1 = []
        self.dataA2 = []
        self.dataTime = []
        self.t0 = time.time()

    def stop(self):
        """
         stops the thread
         not in use at the moment. Setting it will stop readouts, as
         there is a check in self.run()
        """
        print('stopping')
        self.continue_run = False

    def run(self):
        while self.continue_run:
            self.feedbackLoop()
            self.finished.emit()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    gui = dsl_gui()
    gui.setWindowTitle('P07 Interferometer GUI')
    gui.show()
    app.exec()
