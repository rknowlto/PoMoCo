from Tkinter import *
from tkFileDialog   import askopenfile
from tkFileDialog   import asksaveasfile

import ConfigParser
from servotorComm import runMovement
from robot import kinematicRobot

##from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
##from matplotlib.figure import Figure
##from matplotlib import cm
##import matplotlib.pyplot as plt
import numpy as np
import math
import pygame
import os
import sys
import time
import string

import pyaudio
import wave
import cPickle
from random import random
from  tkMessageBox    import askretrycancel


#########################################################################################################################
#########################################################################################################################
class App:

    def __init__(self, master, controller):
        self.con = controller
        self.master = master

        self.frame = Frame(self.master,width = 1000)
        self.frame.pack()

        # Setup names and servo assignment ###############################################################
        self.Dict = [
            ("LF hip", 7),
            ("LF knee", 6),
            ("LF ankle", 5),
            ("LM hip", 11),
            ("LM knee", 10),
            ("LM ankle", 9),
            ("LB hip", 15),
            ("LB knee", 14),
            ("LB ankle", 13),
            ("RF hip", 24),
            ("RF knee", 25),
            ("RF ankle", 26),
            ("RM hip", 20),
            ("RM knee", 21),
            ("RM ankle", 22),
            ("RB hip", 16),
            ("RB knee", 17),
            ("RB ankle", 18),
            ("Head",31)
        ]
        
        # Setup menu system ##############################################################################
        menu = Menu(root)
        root.config(menu=menu)
        filemenu = Menu(menu)

        menu.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="New")
        filemenu.add_command(label="Save Offsets", command=self.saveOffsets)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.quitApp)
        master.createcommand('exit', self.quitApp)  

        self.addSpace([14,0])

        self.loadOffsets()
          
        # Setup main control buttons ####################################################################
        self.killButton = Button(self.frame, text="Kill All Servos",fg="red",
                                font=("Helvetica", 20),command=self.estop)
        self.killButton.grid(row=0, column=15, rowspan = 3, columnspan = 2)

        self.addSpace([18,0])
        Label(self.frame, text="   ").grid(row=0, column=21)  
        # create offset controls
        self.dB_Calibrate = Button(self.frame, text="Calibrate offsets", font=("Tahoma", 10), width = 18, command=self.ServoCalibration)
        self.dB_Calibrate.grid(row = 0, column = 20, rowspan = 1, sticky = N)
        self.OffsetControls = groupOffsetControl(self.frame, self.con, self.Dict, colX = 25, rowY = 0)

        # create manual controls
        self.dB_ManualContol = Button(self.frame, text="Manual control",    font=("Tahoma", 10), width = 18, command=self.ManualControl)
        self.dB_ManualContol.grid(row = 1, column = 20, rowspan = 1, sticky = N)
        self.ManualControls = groupManualControl(self.frame, self.con, self.Dict, colX = 25, rowY = 0)

        # create kinematic control 
        self.dB_KinematicContol = Button(self.frame, text="Kinematic control", font=("Tahoma", 10), width = 18, command=self.KinematicControl)
        self.dB_KinematicContol.grid(row = 2, column = 20, rowspan = 1, sticky = N)
        self.KinematicControls = groupKinematicControl(self.frame, self.con, self.Dict, colX = 25, rowY = 0)

        # create drawings control 
        self.dB_DrawingControl = Button(self.frame, text="Drawing", font=("Tahoma", 10), width = 18, command=self.DrawingControl)
        self.dB_DrawingControl.grid(row = 3, column = 20, rowspan = 1, sticky = N)
        self.DrawingControls = groupDrawingControl(self.frame, self.con, self.Dict, colX = 25, rowY = 0)

        # create dancing control 
        self.dB_DancingControl = Button(self.frame, text="Dancing", font=("Tahoma", 10), width = 18, command=self.DancingControl)
        self.dB_DancingControl.grid(row = 4, column = 20, rowspan = 1, sticky = N)
        self.DancingControls = groupDancingControl(self.frame, self.con, self.Dict, colX = 25, rowY = 0)

        # Generate buttons for all move functions ######################################################
        counter = 0
        for move_name in moves:
            b = Button(self.frame, text=move_name, width = 15)
            b.move_name = move_name
            b.sel = lambda b = b: runMovement(move, b.move_name)
            b.config(command = b.sel)
            b.grid(row = counter/3 + 0, column = counter%3 + 1)
            counter += 1

        # create FPS scale ##############################################################################
        self.FPS = IntVar(value = 30) # set default FPS to 30
        Scale(self.frame, from_= 1, to = 50, length = 150, var = self.FPS, orient = HORIZONTAL).grid(row = counter/3-2, column=16, rowspan = 2, sticky = W)
        Label(self.frame, text = "FPS:", anchor = E).grid(row = counter/3-1, column = 15, sticky = E)
        
        # create second frame with plot window ##########################################################
        self.frame2 = Frame(self.frame,width = 745, height = 550)
        self.frame2.grid(row = counter/3+2, column = 1, rowspan = 100, columnspan = 100, sticky = N+W)
        self.centerPlot = IntVar(value = 1)
        Checkbutton(self.frame, text="Auto center plot", var=self.centerPlot).grid(row=counter/3, column=15, columnspan = 2)
                 
        # Create robot figure
        self.virtualRobot = virtualRobot(self.frame2, self.con, self.Dict)
        
        # finish frame design
        self.frame.pack()


        self.tend2 = 0
        # run infine loop
        self.poll()

        # kill
        self.estop()

    #######################################################################################################
    def loadOffsets(self):
        # If there is one offset file in the folder, automatically load it
        off_files = []
        for filename in os.listdir(os.getcwd()):
            start, ext = os.path.splitext(filename)
            if ext == '.cfg':
                off_files.append(filename)

        if len(off_files) == 1:
            print "Opening",off_files[0]
            config = ConfigParser.ConfigParser()
            config.read(off_files[0])

            try:
                data = config.items('offsets')
                for line in data:
                    servoNum = int(line[0])
                    offset = line[1]
                    offset = string.strip(offset,"[] ")
                    offset = np.int_(string.split(offset,', '))
                    for servo in self.con.servos:
                        if self.con.servos[servo].servoNum == servoNum:
                            for j in range(len(offset)):    
                                self.con.servos[servo].setOffset(timing = offset[j], index = j)
                            break
                print "Automatically loaded offsets from",off_files[0]
            except:
                print "Automatic offset load failed, is there an offset file in the program directory?"

    def saveOffsets(self):
        cfgFile = asksaveasfile(filetypes = [('CFG', '*.cfg'),("All Files",".*")], defaultextension=".cfg")
        config = ConfigParser.ConfigParser()
        config.add_section("offsets")
        for i in range(len(self.con.servos)):
            offset = []
            for j in range(7):
                offset.append(int(self.con.servos[i].getOffsetuS(index = j)))
            config.set("offsets", "%.3d"%(i), offset)             
        config.write(cfgFile)

    #######################################################################################################
    def quitApp(self):
        self.con.killAll()
##        plt.close('all')
        root.quit()
##        root.destroy()

    def poll(self):
        # Constantly updates the GUI based on the current status of the controller
        if self.dB_ManualContol.cget('relief') == 'sunken': # if manual control widgets are shown
            for i in range(len(self.ManualControls.servos)):
                self.ManualControls.servos[i].servoPos.set(int(round(self.con.servos[self.Dict[i][1]].getPosDeg())))
                self.ManualControls.servos[i].active.set(self.con.servos[self.Dict[i][1]].getActive())

        self.DrawingControls.Loop()
        self.DancingControls.Loop()
        # draw the robot
        robotPosInc = self.virtualRobot.plot(self.centerPlot.get())
        self.KinematicControls.Loop(robotPosInc)

        if self.DancingControls.on:  # when dancing, the sound grabber defines the timing
            self.master.after(2, self.poll)
        else:
            self.master.after(1000/self.FPS.get(), self.poll)


    def addSpace(self, coords, rowspan = 1, columnspan = 1):
        Label(self.frame, text="\t\t", fg="red").grid(row=coords[1], column=coords[0], rowspan=rowspan, columnspan=columnspan)  

    def estop(self):
        self.con.killAll()

    def ServoCalibration(self):
        if self.dB_Calibrate.cget('relief') == RAISED:
            self.dB_Calibrate.config(relief = SUNKEN)
            self.dB_ManualContol.config(state = DISABLED)
            self.dB_KinematicContol.config(state = DISABLED)
            self.dB_DrawingControl.config(state = DISABLED)
            self.dB_DancingControl.config(state = DISABLED)

            self.con.killAll()
            self.OffsetControls.show()
            
        else:
            self.dB_Calibrate.config(relief = RAISED)
            self.dB_ManualContol.config(state = NORMAL)
            self.dB_KinematicContol.config(state = NORMAL)
            self.dB_DrawingControl.config(state = NORMAL)
            self.dB_DancingControl.config(state = NORMAL)

            self.con.killAll()
            self.OffsetControls.hide()

    def ManualControl(self):
        if self.dB_ManualContol.cget('relief') == RAISED:
            self.dB_ManualContol.config(relief = SUNKEN)
            self.dB_Calibrate.config(state = DISABLED)
            self.dB_KinematicContol.config(state = DISABLED)
            self.dB_DrawingControl.config(state = DISABLED)
            self.dB_DancingControl.config(state = DISABLED)

            self.ManualControls.show()

        else:
            self.dB_ManualContol.config(relief = RAISED)
            self.dB_Calibrate.config(state = NORMAL)
            self.dB_KinematicContol.config(state = NORMAL)
            self.dB_DrawingControl.config(state = NORMAL)
            self.dB_DancingControl.config(state = NORMAL)

            self.con.killAll()
            self.ManualControls.hide()

    def KinematicControl(self):
        if self.dB_KinematicContol.cget('relief') == RAISED:
            self.dB_KinematicContol.config(relief = SUNKEN)
            self.dB_ManualContol.config(state = DISABLED)
            self.dB_Calibrate.config(state = DISABLED)
            self.dB_DrawingControl.config(state = DISABLED)
            self.dB_DancingControl.config(state = DISABLED)
    
            self.KinematicControls.show()

        else:
            self.dB_KinematicContol.config(relief = RAISED)
            self.dB_Calibrate.config(state = NORMAL)
            self.dB_ManualContol.config(state = NORMAL)
            self.dB_DrawingControl.config(state = NORMAL)
            self.dB_DancingControl.config(state = NORMAL)

            self.con.killAll()
            self.KinematicControls.hide()
            
    def DrawingControl(self):
        if self.dB_DrawingControl.cget('relief') == RAISED:
            self.dB_DrawingControl.config(relief = SUNKEN)
            self.dB_KinematicContol.config(state = DISABLED)
            self.dB_ManualContol.config(state = DISABLED)
            self.dB_Calibrate.config(state = DISABLED)
            self.dB_DancingControl.config(state = DISABLED)
        
            self.DrawingControls.show()

        else:
            self.dB_DrawingControl.config(relief = RAISED)
            self.dB_KinematicContol.config(state = NORMAL)
            self.dB_Calibrate.config(state = NORMAL)
            self.dB_ManualContol.config(state = NORMAL)
            self.dB_DancingControl.config(state = NORMAL)
            

            self.DrawingControls.hide()
            
    def DancingControl(self):
        if self.dB_DancingControl.cget('relief') == RAISED:
            self.dB_DancingControl.config(relief = SUNKEN)
            self.dB_KinematicContol.config(state = DISABLED)
            self.dB_ManualContol.config(state = DISABLED)
            self.dB_Calibrate.config(state = DISABLED)
            self.dB_DrawingControl.config(state = DISABLED)

            self.DancingControls.show()
            

        else:
            self.dB_DancingControl.config(relief = RAISED)
            self.dB_KinematicContol.config(state = NORMAL)
            self.dB_Calibrate.config(state = NORMAL)
            self.dB_ManualContol.config(state = NORMAL)
            self.dB_DrawingControl.config(state = NORMAL)
            
            self.DancingControls.hide()
            

#########################################################################################################################
# create GUI for servo offset calibration
# by Michal G., 20-05-2013
#########################################################################################################################
class groupOffsetControl:
    def __init__(self, frame, con, Dict, rowY = 0, colX = 0):
        self.frame = Frame(frame,width = 1000, height = 500)#, bg = 'blue')
        self.con = con
        self.rowY = rowY
        self.colX = colX
        self.Dict = Dict           
        self.nrServo = IntVar(value = -1)
        self.nrOffset = IntVar(value = 3)
        self.activeServo = -1
        self.activeOffset = 3
        self.rangeOffsets = [-80,-60,-30,0,30,60,80]
 
        # radio buttons for servo selection
        self.addSpace([0,0])
        Radiobutton(self.frame, text = "", variable = self.nrServo, value = -1, command = self.pickServo).grid(row = 2, column = 2)
        Label(self.frame,text = "OFF", font = ("Tahoma", 10,"bold"), anchor = W).grid(row = 2, column = 1, sticky = W)
        self.addSpace([5,0])
        for i, (text, value) in zip(range(len(Dict)),Dict):
            Radiobutton(self.frame, text = "", variable = self.nrServo, value = i, command = self.pickServo).grid(row = i+6 + i/3, column = 2)
            Label(self.frame, text = text, font = ("Tahoma", 10,"bold"), anchor = W).grid(row = i+6 + i/3, column = 1, sticky = W)
        self.addSpace([9,0])
        self.addSpace([13,0])
        self.addSpace([17,0])
        self.addSpace([21,0])
        self.addSpace([25,0])
        self.addSpace([29,0])

        # radio buttons for offset selection
        for (j, text) in zip(range(7),self.rangeOffsets):
            Radiobutton(self.frame, text = "", variable = self.nrOffset, value = j, command = self.pickServo).grid(row = 4, column = j+4)
            Label(self.frame, text = str(text), font = ("Tahoma", 10,"bold"), width = 8).grid(row = 3, column = j+4)

        # labels
        self.labelOffsetVar = []
        self.labelOffset = []
        for i in range(len(Dict)):
            variables = []
            labels = []
            for j in range(7):
                var = StringVar()
                var.set(int(round(self.con.servos[self.Dict[i][1]].getOffsetDeg(index = j))))
                variables.append(var)
                l = Label(self.frame, textvariable = var, font = ("Tahoma", 10))
                l.grid(row = i+6 + i/3, column = j+4)
                labels.append(l)
            self.labelOffsetVar.append(variables)
            self.labelOffset.append(labels)                             

        self.addSpace([31,0])
        
        #offset plus
        Button(self.frame, text="+", font = ("Tahoma", 12, "bold"), width = 6, command=self.offsetInc).grid(row=0, column=6)

        #offset minus
        Button(self.frame, text="-", font = ("Tahoma", 12, "bold"), width = 6, command=self.offsetDec).grid(row=0, column=7)

    def addSpace(self, coords):
        Label(self.frame, text="\t\t", fg="red").grid(row=coords[0], column=coords[1])

    def pickServo(self):
        self.labelOffset[self.activeServo][self.activeOffset].config(font = ("Tahoma", 10), fg = "black")
        self.con.servos[self.Dict[self.activeServo][1]].kill()
        
        self.activeServo = self.nrServo.get()
        self.activeOffset = self.nrOffset.get()
        
        if self.activeServo <> -1:
            self.labelOffset[self.activeServo][self.activeOffset].config(font = ("Tahoma", 10,"bold"), fg = "red")
            self.con.servos[self.Dict[self.activeServo][1]].setPos(deg = self.rangeOffsets[self.activeOffset])

    def offsetInc(self):
        if self.activeServo <> -1:
            offset = self.con.servos[self.Dict[self.activeServo][1]].getOffsetDeg(index = self.activeOffset) + 1         
            self.labelOffsetVar[self.activeServo][self.activeOffset].set(int(offset))
            self.con.servos[self.Dict[self.activeServo][1]].setOffset(deg = offset, index = self.activeOffset)
            self.con.servos[self.Dict[self.activeServo][1]].move()

    def offsetDec(self):
        if self.activeServo <> -1:
            offset = self.con.servos[self.Dict[self.activeServo][1]].getOffsetDeg(index = self.activeOffset) - 1        
            self.labelOffsetVar[self.activeServo][self.activeOffset].set(int(offset))
            self.con.servos[self.Dict[self.activeServo][1]].setOffset(deg = offset, index = self.activeOffset)
            self.con.servos[self.Dict[self.activeServo][1]].move()
        

    def show(self):
        self.activeServo = -1
        self.activeOffset = 3
        self.nrServo.set(-1)
        self.nrOffset.set(3)
        self.frame.grid(row = self.rowY, column = self.colX, rowspan = 100, columnspan = 100, sticky = N+W)
        
    def hide(self):
        self.frame.grid_forget()


#########################################################################################################################
# create GUI for manual servo control
#########################################################################################################################
class groupManualControl:
    def __init__(self, frame, con, Dict, rowY = 0, colX = 0):
        self.frame = Frame(frame,width = 1000, height = 500)
        self.con = con
        self.rowY = rowY
        self.colX = colX
        self.Dict = Dict
        self.servos = []
        
        self.addSpace([0,0])
        self.servos.append(servoManualControl(self.frame, self.con, servoNum = Dict[0][1], name = Dict[0][0], colX = 1, rowY = 3)) 
        self.servos.append(servoManualControl(self.frame, self.con, servoNum = Dict[1][1], name = Dict[1][0], colX = 1, rowY = 4))
        self.servos.append(servoManualControl(self.frame, self.con, servoNum = Dict[2][1], name = Dict[2][0], colX = 1, rowY = 5))
        self.addSpace([1,6])
        self.servos.append(servoManualControl(self.frame, self.con, servoNum = Dict[3][1], name = Dict[3][0], colX = 1, rowY = 7)) 
        self.servos.append(servoManualControl(self.frame, self.con, servoNum = Dict[4][1], name = Dict[4][0], colX = 1, rowY = 8))
        self.servos.append(servoManualControl(self.frame, self.con, servoNum = Dict[5][1], name = Dict[5][0], colX = 1, rowY = 9))
        self.addSpace([1,10])
        self.servos.append(servoManualControl(self.frame, self.con, servoNum = Dict[6][1], name = Dict[6][0], colX = 1, rowY = 11)) 
        self.servos.append(servoManualControl(self.frame, self.con, servoNum = Dict[7][1], name = Dict[7][0], colX = 1, rowY = 12))
        self.servos.append(servoManualControl(self.frame, self.con, servoNum = Dict[8][1], name = Dict[8][0], colX = 1, rowY = 13))
        
        self.servos.append(servoManualControl(self.frame, self.con, servoNum = Dict[9][1], name = Dict[9][0], colX = 11, rowY = 3)) 
        self.servos.append(servoManualControl(self.frame, self.con, servoNum = Dict[10][1], name = Dict[10][0], colX = 11, rowY = 4))
        self.servos.append(servoManualControl(self.frame, self.con, servoNum = Dict[11][1], name = Dict[11][0], colX = 11, rowY = 5))
        
        self.servos.append(servoManualControl(self.frame, self.con, servoNum = Dict[12][1], name = Dict[12][0], colX = 11, rowY = 7)) 
        self.servos.append(servoManualControl(self.frame, self.con, servoNum = Dict[13][1], name = Dict[13][0], colX = 11, rowY = 8))
        self.servos.append(servoManualControl(self.frame, self.con, servoNum = Dict[14][1], name = Dict[14][0], colX = 11, rowY = 9))
        
        self.servos.append(servoManualControl(self.frame, self.con, servoNum = Dict[15][1], name = Dict[15][0], colX = 11, rowY = 11)) 
        self.servos.append(servoManualControl(self.frame, self.con, servoNum = Dict[16][1], name = Dict[16][0], colX = 11, rowY = 12))
        self.servos.append(servoManualControl(self.frame, self.con, servoNum = Dict[17][1], name = Dict[17][0], colX = 11, rowY = 13))
        self.addSpace([0,14])
        self.servos.append(servoManualControl(self.frame, self.con, servoNum = Dict[18][1], name = Dict[18][0], colX = 1, rowY = 15)) 
        
        
    def addSpace(self, coords):
        Label(self.frame, text="\t\t", fg="red").grid(column=coords[0], row=coords[1])

    def show(self):
        self.frame.grid(row = self.rowY, column = self.colX, rowspan = 100, columnspan = 100, sticky = N+W)
        
    def hide(self):
        self.frame.grid_forget()
                
#########################################################################################################################
class servoManualControl:
    def __init__(self,frame, con, servoNum, name = "None", rowY=0, colX=0):
        self.frame = frame
        self.con = con
        self.active = IntVar(value = 0)
        self.servoPos = IntVar(value = int(round(self.con.servos[servoNum].getPosDeg())))
        self.servoNum = servoNum

        Label(self.frame, text = name).grid(row = rowY, column = 0 + colX)   
        Checkbutton(self.frame, text = "On", var = self.active, command = self.checkServo).grid(row = rowY, column = 1 + colX)
        Button(self.frame, text = "Reset", command = self.resetServo).grid(row = rowY, column = 2 + colX)
        Scale(self.frame, from_= -90, to = 90, length = 200, orient = HORIZONTAL, showvalue = 0, var = self.servoPos, command = self.moveServo).grid(row = rowY, column = 3 + colX)
        Label(self.frame, textvariable = self.servoPos, width = 8, anchor = W).grid(row = rowY, column= 4 + colX, sticky = W)
        
    def checkServo(self):
        if self.active.get() == 0:
            self.con.servos[self.servoNum].kill()
        else:
            self.con.servos[self.servoNum].setPos(deg = self.servoPos.get())

    def moveServo(self,newServoPos):
        if self.active.get():
            self.con.servos[self.servoNum].setPos(deg = int(newServoPos))
            self.servoPos.set(int(newServoPos))
            
    def resetServo(self):
        self.con.servos[self.servoNum].reset()
        self.servoPos.set(int(round(self.con.servos[self.servoNum].getPosDeg())))
       
#########################################################################################################################
# create GUI for inverse-kinematic conrol
# by Michal G., 15-06-2013
#########################################################################################################################
class groupKinematicControl:
    def __init__(self, frame, con, Dict, rowY = 0, colX = 0):
        self.frame = Frame(frame,width = 1000, height = 500)
        self.con = con
        self.rowY = rowY
        self.colX = colX
        self.Dict = Dict
        self.on = False                     
        self.iRx = IntVar()
        self.iRy = IntVar()
        self.iZ = IntVar(value = 75)
        self.iYRz = IntVar()
        self.dPos = [0,0,0]
        self.pos = [0,0,self.iZ.get()]
        self.posOld = [0,0,self.iZ.get()]
        self.angle = [0,0,0]
        self.angleOld = [0,0,0]
        self.moveEnabled = IntVar()
        self.move = False
        self.once = False
        self.stringYRz = StringVar(value = 'Rz:')
        self.iMovingLegs = IntVar(value = 3)
        self.sliderGain = 3
        self.stringJoystick = StringVar()
        self.scanDistance = StringVar(value = '0.00')
        self.robotPosStr = StringVar()
        self.imageData = np.zeros((500,400)) + 0.5

        self.scaleZ = Scale(self.frame, from_= 100, to = 35, length = 200, showvalue = 0, var = self.iZ, activebackground = 'blue')
        self.scaleZ.grid(row = 2, column = 1, rowspan = 5)
        Label(self.frame, textvariable = self.iZ, width = 3, font=('Tahoma', 10,'bold')).grid(row = 3, column = 0)

        self.scaleYRz = Scale(self.frame, from_= -20, to = 20, length = 200, orient = HORIZONTAL, showvalue = 0, var = self.iYRz, activebackground = 'blue', bg = '#008', command = self.SliderYRzClick)
        self.scaleYRz.grid(row = 1, column = 2)
        self.labelYRz = Label(self.frame, textvariable = self.iYRz, width = 3, font=('Tahoma', 10,'bold'))
        self.labelYRz.grid(row = 0, column = 2)
        self.scaleYRz.bind("<ButtonRelease-1>", self.LeftClick_release)

        self.scaleRx = Scale(self.frame, from_= -20, to = 20, length = 200, orient = HORIZONTAL, showvalue = 0, var = self.iRx, activebackground = 'blue')
        self.scaleRx.grid(row = 7, column = 2)
        Label(self.frame, textvariable = self.iRx, width = 3, font=('Tahoma', 10,'bold')).grid(row = 8, column = 2)

        self.scaleRy = Scale(self.frame, from_= 20, to = -20, length = 200, showvalue = 0, var = self.iRy, activebackground = 'blue')
        self.scaleRy.grid(row = 2, column = 3, rowspan = 5)
        Label(self.frame, textvariable = self.iRy, width = 3, font=('Tahoma', 10,'bold')).grid(row = 3, column = 4)

        Label(self.frame, textvariable = self.stringYRz , font=('Tahoma', 10,'bold')).place(x = 120, y = 0)
        Label(self.frame, text = 'Z:', font=('Tahoma', 10,'bold')).place(x = 8, y = 100)
        Label(self.frame, text = 'Rx:', font=('Tahoma', 10,'bold')).place(x = 120, y = 274)
        Label(self.frame, text = 'Ry:', font=('Tahoma', 10,'bold')).place(x = 285, y = 100)

        Scale(self.frame, from_= 1, to = 3, length = 70, orient = HORIZONTAL, showvalue = 0, var = self.iMovingLegs, command = self.SliderMovingLegs).grid(row = 1, column = 5, sticky = E)
        Label(self.frame, textvariable = self.iMovingLegs, width = 3, font=('Tahoma', 10,'bold')).grid(row = 1, column = 6, sticky = W)
        
        
        Button(self.frame, text = 'Center', width = 10, command = self.ResetPosition).grid(row = 2, column = 5)
        Checkbutton(self.frame, text = 'Enable move', var = self.moveEnabled, command = self.SwapControls).grid(row = 2, column = 6)

        self.labelJoystick = Label(self.frame, textvariable = self.stringJoystick, width = 30, height = 5, font=('Tahoma', 10,'bold'))
        self.labelJoystick.grid(row = 3, column = 5, columnspan = 2)

        # create custom GUI item
        self.pad = Canvas(self.frame, width = 200, height = 200, cursor = 'circle')
        self.rectangle = self.pad.create_rectangle(3,3,201,201, width = 2, outline = '#008')
        self.pad.create_line(101,5,101,201, width = 1, dash = (5,5))
        self.pad.create_line(5,101,201,101, width = 1, dash = (5,5))
        self.circle = self.pad.create_oval(85,85,115,115, fill = '#008', outline = '#00F', width = 2)
        self.textX = self.pad.create_text(110, 5, text = 'X = 0', anchor = NW, font=('Tahoma', 10,'bold'))
        self.textYRz = self.pad.create_text(8, 95, text = 'Y = 0',anchor = SW, font=('Tahoma', 10,'bold'))
        self.pad.bind("<B1-Motion>", self.LeftClick)
        self.pad.bind("<B3-Motion>", self.RightClick)
        self.pad.bind("<Button-1>", self.LeftClick)
        self.pad.bind("<Button-3>", self.RightClick)
        self.pad.bind("<ButtonRelease-1>", self.LeftClick_release)
        self.pad.bind("<ButtonRelease-3>", self.RightClick_release)
        self.pad.grid(row = 2, column = 2, rowspan = 5)

        

##        # area scan and coordination
##        Button(self.frame, text = 'Scan', width = 10, command = self.ScanArea).grid(row = 4, column = 5)
##        Label(self.frame, textvariable = self.scanDistance , font=('Tahoma', 10,'bold')).grid(row = 4, column = 6)
##        Label(self.frame, textvariable = self.robotPosStr , font=('Tahoma', 10,'bold')).grid(row = 5, column = 5, columnspan = 2)
##        self.robotPos = np.array([0,0,0], dtype = float)
##        
##        self.frame2 = Frame(self.frame,width = 500, height = 400)
##        self.frame2.grid(row = 14, column = 0, columnspan = 10)
##        
##        self.fig = plt.figure()
##        plt.subplots_adjust(left = 0, right = 1.0, top = 1.0, bottom = 0)
##        
##        self.canvas = FigureCanvasTkAgg(self.fig, master = self.frame2)
##        self.canvas._tkcanvas.place(x = 0, y = 0, width = 500, height = 400)
##        
##        self.subPlot = self.fig.add_subplot(111)
##        self.subPlot.get_yaxis().set_visible(False)
##        self.subPlot.get_xaxis().set_visible(False)
##        self.subPlot.get_axes().set_frame_on(False)
##        self.im = self.subPlot.imshow(self.imageData.T, cmap=cm.RdBu_r, origin='lower', vmin = 0, vmax = 1)
##        self.triangle = np.array([[-5,-5],[10,0],[-5,5],[-5,-5]])
##        t = self.triangle + [250,200]
##        self.robotCursor = self.subPlot.plot(t[:,0], t[:,1], lw = 2, c = 'y')[0]
##        self.subPlot.set_xlim((0,500))
##        self.subPlot.set_ylim((0,400))

        self.Robot = kinematicRobot(con, Dict)

        # joystick initialization
        pygame.init()
        self.isJoystick = (pygame.joystick.get_count() > 0)
        if self.isJoystick:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            self.stringJoystick.set('Joystick active')
        else:
            self.labelJoystick.configure(fg = 'red')
            self.stringJoystick.set('No joystick')
        self.jAxisWasMove = False
        self.jAxisWasTilt = False

    def Loop(self, robotPosInc):
        if self.on:
##            self.robotPos[0:2] += self.RotZ(robotPosInc[0:2], self.robotPos[2] + robotPosInc[2]/2)
##            self.robotPos[2] += robotPosInc[2]
##            self.robotPosStr.set("X: %1.1f, Y: %1.1f, Rz: %1.2f" % (self.robotPos[0],self.robotPos[1],self.robotPos[2]))
##            t = self.RotZ(self.triangle.T,self.robotPos[2]).T + self.robotPos[0:2]/10.0 + [250,200]        
##            self.robotCursor.set_data(t[:,0],t[:,1])
##            self.canvas.draw()
            
            if self.isJoystick:
                pygame.event.pump() # update joystick events
                axisX = self.joystick.get_axis(1)
                axisY = self.joystick.get_axis(0)
                axisRx = self.joystick.get_axis(4)
                axisRy = self.joystick.get_axis(3)
                axisRz = self.joystick.get_axis(2)
                self.stringJoystick.set("X: %1.3f, Y: %1.3f\nRx: %1.3f, Ry: %1.3f, Rz: %1.3f" %(axisX, axisY, axisRx, axisRy, axisRz))

                jAxisTilt = np.abs(np.array([axisRx, axisRy]))
                if (jAxisTilt > 0.015).any() or self.jAxisWasTilt:
                    self.iRx.set(int(round(axisRx*15)))
                    self.iRy.set(-int(round(axisRy*15)))
                    self.jAxisWasTilt = (jAxisTilt > 0.015).any()

                jAxisMove = np.abs(np.array([axisX, axisY, axisRz]))
                if (jAxisMove > 0.015).any() or self.jAxisWasMove:
                    self.dPos = [axisX*4.5*self.sliderGain, axisY*4*self.sliderGain, -axisRz*2*self.sliderGain]
                    self.move = True
                    self.jAxisWasMove = (jAxisMove > 0.015).any()
                    if not (jAxisMove > 0.015).any():
                        self.dPos = [0, 0, 0]
                        self.move = False
                        self.once = True               

                hat = self.joystick.get_hat(0)
                self.pos[0] += 5*hat[1]
                self.pos[1] -= 5*hat[0]
                self.iZ.set(self.iZ.get() + 2*self.joystick.get_button(3) - 2*self.joystick.get_button(0))
                self.angle[2] += 2*self.joystick.get_button(4) - 2*self.joystick.get_button(5)

                if self.joystick.get_button(1):
                    self.iRx.set(0)
                    self.iRy.set(0)
                    self.iYRz.set(0)
                    self.pos[0] = 0
                    self.pos[1] = 0
                    self.angle[2] = 0

            self.pos[2] = self.iZ.get()
            self.angle[0] = self.iRx.get()
            self.angle[1] = self.iRy.get()

            # if the desired position or angle changed, update robot
            if  (self.pos != self.posOld) or (self.angle != self.angleOld):
                self.once = True

            self.posOld[0:3] = self.pos[0:3]
            self.angleOld[0:3] = self.angle[0:3]

            if self.moveEnabled.get():
                self.pad.itemconfigure(self.circle, fill = '#800')
                self.pad.itemconfigure(self.textX, text = ('dX: %1.1f' % self.dPos[0]))
                self.pad.itemconfigure(self.textYRz, text = ('dRz: %1.1f' % self.dPos[2]))
                self.pad.coords(self.circle, self.dPos[2]*50/self.sliderGain + 85, self.dPos[0]*20/self.sliderGain + 85, self.dPos[2]*50/self.sliderGain + 115, self.dPos[0]*20/self.sliderGain + 115)
            else:
                self.pad.itemconfigure(self.circle, fill = '#008')
                self.pad.itemconfigure(self.textX, text = ('X: %d' % self.pos[0]))
                self.pad.itemconfigure(self.textYRz, text = ('Y: %d' % self.pos[1]))
                self.pad.coords(self.circle, -self.pos[1]*2 + 85, -self.pos[0]*2 + 85, -self.pos[1]*2 + 115, -self.pos[0]*2 + 115)

            # call robot update
            if self.once or self.move:  
                self.Robot.updateRobot(self.pos, self.angle, self.move, self.dPos)
                if self.move == False:
                    self.once = False

    def SliderMovingLegs(self, event):
            self.Robot.setMovingLegs(self.iMovingLegs.get())
            self.sliderGain = self.iMovingLegs.get()
            if self.moveEnabled.get():
                self.scaleYRz.configure(from_= -4*self.sliderGain, to = 4*self.sliderGain)
     

    def SliderYRzClick(self, event):
        if self.moveEnabled.get():
            self.dPos[1] = self.iYRz.get()
            self.move = True
        else:
            self.angle[2] = self.iYRz.get()

    def LeftClick(self, event):
        if (event.x > 5) and (event.x < 195) and (event.y > 5) and (event.y < 195):
            if self.moveEnabled.get():
                self.dPos = [-(101 - event.y)/20.0*self.sliderGain, 0, -(101 - event.x)/50.0*self.sliderGain]
                self.move = True
            else:
                self.pos[0] = (101 - event.y)/2.0
                self.pos[1] = (101 - event.x)/2.0
            

    def LeftClick_release(self, event):
        if self.moveEnabled.get():
            self.pad.itemconfigure(self.circle, fill = '#800')
            self.iYRz.set(0)
        else:
            self.pad.itemconfigure(self.circle, fill = '#008')
        self.dPos = [0,0,0]
        self.move = False
        self.once = True

    def RightClick(self, event):
        self.pad.configure(cursor = 'cross')
        self.scaleRx.configure(state = 'active')
        self.scaleRy.configure(state = 'active')
        self.iRx.set(int((event.x - 101)/4.5))
        self.iRy.set(int(-(event.y - 101)/4.5))
        self.angle[0] = self.iRx.get()
        self.angle[1] = self.iRy.get()

    def RightClick_release(self, event):
        self.pad.configure(cursor = 'circle')
        self.scaleRx.configure(state = 'normal')
        self.scaleRy.configure(state = 'normal')

    def ResetPosition(self):
        self.iRx.set(0)
        self.iRy.set(0)
        self.iYRz.set(0)
        self.pos[0] = 0
        self.pos[1] = 0
        self.angle = [0,0,0]

##    def RotZ(self,pos,angle):
##        Rz = [[np.cos(angle),-np.sin(angle)],
##              [np.sin(angle),np.cos(angle)]]
##        return np.dot(Rz,pos)    
##
##    def fillTriangle(self, t, add = True):
##        minX = int(np.maximum(min(t[:,0]),0))
##        maxX = int(np.minimum(max(t[:,0]),500))
##        for x in range(minX,maxX):
##            x = float(x)
##            y = [np.nan,np.nan,np.nan]
##            n = -1
##            if t[1,0] != t[0,0]:
##                n = (x - t[0,0])/(t[1,0] - t[0,0])
##            if n >= 0 and n <= 1:
##                y[0] = int(n*(t[1,1] - t[0,1])) + t[0,1]
##
##            n = -1
##            if t[2,0] != t[0,0]:    
##                n = (x - t[0,0])/(t[2,0]-t[0,0])    
##            if n >= 0 and n <= 1:
##                y[1] = int(n*(t[2,1] - t[0,1])) + t[0,1]
##
##            n = -1
##            if t[2,0] != t[1,0]:
##                n = (x - t[1,0])/(t[2,0]-t[1,0])    
##            if n >= 0 and n <= 1:
##                y[2] = int(n*(t[2,1] - t[1,1])) + t[1,1]
##
##            y = np.sort(y)
##            if not np.isnan(y[0:2]).any():
##                y = np.minimum(y,399)
##                y = np.maximum(y,0)
##                if add:
##                    self.imageData[x,y[0]:y[1]] = np.minimum(self.imageData[x,y[0]:y[1]] + 0.2, 1)
##                else:
##                    self.imageData[x,y[0]:y[1]] = np.maximum(self.imageData[x,y[0]:y[1]] - 0.4, 0)
##
##
##    def fillScan(self, p0, angle, dist):
##        p1 = p0 + 5*dist*self.RotZ([1,0], angle - np.pi/16)
##        p2 = p0 + 5*dist*self.RotZ([1,0], angle + np.pi/16)
##        t = np.array([p0,p1,p2])
##        self.fillTriangle(t, True)
##        
##        p1 = p0 + 0.9*dist*self.RotZ([1,0], angle - np.pi/16)
##        p2 = p0 + 0.9*dist*self.RotZ([1,0], angle + np.pi/16)
##        t = np.array([p0,p1,p2])
##        self.fillTriangle(t, False)
##
##    def ScanArea(self):
##        self.con.serialHandler.recieveQueue = [] # clear queue
##        self.con.serialHandler.sendLock.acquire()
##        self.con.serialHandler.sendQueue.append("S")
##        self.con.serialHandler.sendLock.release()
##        i = 0
##        while (self.con.serialHandler.recieveQueue == 0) or (i < 20):
##            time.sleep(0.1)
##            i += 1
##        for i in range(9):
##            if self.con.serialHandler.recieveQueue > 0:
##                dist = float(self.con.serialHandler.recieveQueue.pop(0))
##                self.scanDistance.set(str(dist))
##                self.fillScan(self.robotPos[0:2]/10 + [250,200], self.robotPos[2] + np.pi*(i/8.0 - 0.5), dist)
##        self.im.set_array(self.imageData.T)
##        self.canvas.draw()
        

    def SwapControls(self):
        self.iYRz.set(0)
        if self.moveEnabled.get():
            self.pad.coords(self.circle,85,85,115,115)
            self.pad.itemconfigure(self.circle, outline = '#A44')
            self.pad.itemconfigure(self.circle, fill = '#800')
            self.scaleYRz.configure(activebackground = 'red', bg = '#800')
            self.scaleYRz.configure(from_= -4*self.sliderGain, to = 4*self.sliderGain)
            self.pad.itemconfigure(self.rectangle, outline = '#800')
            self.stringYRz.set('Y:')
            self.pos[0] = 0
            self.pos[1] = 0
            self.angle[2] = 0
        else:
            self.pad.itemconfigure(self.circle, outline = '#44A')
            self.pad.itemconfigure(self.circle, fill = '#008')
            self.scaleYRz.configure(activebackground = 'blue', bg = '#008')
            self.scaleYRz.configure(from_= -20, to = 20)
            self.pad.itemconfigure(self.rectangle, outline = '#008')
            self.stringYRz.set('Rz:')
            self.pos[0] = 0
            self.pos[1] = 0
            self.angle[2] = 0

    def show(self):
        self.frame.grid(row = self.rowY, column = self.colX, rowspan = 100, columnspan = 100, sticky = N+W)
        self.Robot.initRobot(self.pos[2])
        self.on = True
        
    def hide(self):
        self.frame.grid_forget()
        self.on = False
        
#########################################################################################################################
# create and plot Kinematic model of the robot
# by Michal G., 05-07-2013
# - updated, now without matplotlib and about 100x faster
#########################################################################################################################
class virtualRobot:
    def __init__(self, frame, con, Dict):
        self.con = con
        self.frame = frame
        self.canvas = Canvas(self.frame, width = 745, height = 550, bg = 'white')
        self.canvas.bind("<B1-Motion>", self.LeftClickMove)
        self.canvas.bind("<B3-Motion>", self.RightClickMove)
        self.canvas.bind("<Button-1>", self.MouseClick)
        self.canvas.bind("<Button-3>", self.MouseClick)
        self.canvas.bind("<ButtonRelease-1>", self.LeftClickRelease)
        self.canvas.bind("<ButtonRelease-3>", self.RightClickRelease)
        self.canvas.grid()

        self.plane = np.array([[-200,-200,0],[200,-200,0],[200,200,0],[-200,200,0]])
        # create floor
        self.planePlot = self.canvas.create_polygon((0,0,0,0,0,0), width = 2, fill ='#EAEAEA', outline = 'black')
        self.gridxPlots = []
        self.gridyPlots = []
        self.gridx = np.zeros((16,3))
        self.gridy = np.zeros((16,3))
        for i in range(8):
            self.gridxPlots.append(self.canvas.create_line((0,0,0,0), fill = '#555'))
            self.gridyPlots.append(self.canvas.create_line((0,0,0,0), fill = '#555'))
            self.gridx[i*2:i*2+2] = [[-200+i*50, -200, 0], [-200+i*50, 200 ,0]]
            self.gridy[i*2:i*2+2] = [[-200, -200+i*50, 0], [200, -200+i*50 ,0]]

        # create robot plot
        self.legPlots = []
        for i in range(6):
            self.legPlots.append(self.canvas.create_line((0,0,0,0), width = 8, fill = 'red'))
        self.bodyPlot = self.canvas.create_polygon((0,0,0,0), width = 8, outline = 'blue', fill = '')
        self.headPlot = self.canvas.create_polygon((0,0,0,0), width = 8, outline = 'darkgreen', fill = '')

        self.canvas.create_rectangle((3,3,745,550), width = 3, outline ='black')

        self.cameraAngle = [-0.5,4.0]
        self.cameraAngleOld = [-0.5,4.0]
        self.cameraZoom = 2500
        self.cameraZoomOld = 2500
        self.mousePos = [0,0]
            
        self.oldCenterPlot = 0
       
        self.bodyRadius = 100
        self.hip = 26
        self.thigh = 49
        self.foot = 55
        self.bodyAngle = 50.0/180*np.pi
        self.bodyAngles = [np.pi/2 - self.bodyAngle, np.pi/2, np.pi/2 + self.bodyAngle,
                          3*np.pi/2 - self.bodyAngle, 3*np.pi/2, 3*np.pi/2 + self.bodyAngle]

        d = self.bodyRadius
        self.body = np.array([[d*np.cos(self.bodyAngles[0]),d*np.sin(self.bodyAngles[0]),0],
                             [d*np.cos(self.bodyAngles[1]),d*np.sin(self.bodyAngles[1]),0],
                             [d*np.cos(self.bodyAngles[2]),d*np.sin(self.bodyAngles[2]),0],
                             [d*np.cos(self.bodyAngles[3]),d*np.sin(self.bodyAngles[3]),0],
                             [d*np.cos(self.bodyAngles[4]),d*np.sin(self.bodyAngles[4]),0],
                             [d*np.cos(self.bodyAngles[5]),d*np.sin(self.bodyAngles[5]),0]]).T
        
        self.head = np.array([[20,20,0],[20,20,40],[20,-20,40],[20,-20,0]]).T
        
        if legsMirrored:
            self.sign = [1,1,1,-1,-1,-1]
        else:
            self.sign = [1,1,1,1,1,1]

        self.Dict = self.reverseDict(Dict)

        self.oldContactB = [False,False,False,False,False,False]
        self.oldContactP = []
        self.oldXYRzVector = np.array([0,0,0], dtype = 'float')


        # possible stable leg combinations (3 legs on the ground)
        self.legCombi = [[0,1,3],[0,1,4],[0,1,5],
                         [0,2,3],[0,2,4],[0,2,5],
                         [1,2,3],[1,2,4],[1,2,5],
                         [0,3,4],[1,3,4],[2,3,4],
                         [0,3,5],[1,3,5],[2,3,5],
                         [0,4,5],[1,4,5],[2,4,5]]

        self.complementaryLegCombi = []
        for i in range(len(self.legCombi)):
            self.complementaryLegCombi.append(filter(lambda x: x not in self.legCombi[i], range(6)))
        
    # internal - reverse dictionary    
    def reverseDict(self,Dict):
        outDict = [] 
        for i in range(9):    # left side from front to back
            outDict.append(Dict[i][1])

        for i in range(3):     # right side from back to front 
            outDict.append(Dict[15-3*i][1])
            outDict.append(Dict[16-3*i][1])
            outDict.append(Dict[17-3*i][1])
            
        outDict.append(Dict[18][1])  # head   
        return outDict

    # internal - check if a point P is inside trinagle P1,P2,P3
    def inTriangle(self, p0, p1, p2, p = [0,0]):
        a = p1[0]-p0[0]
        b = p2[0]-p0[0]
        c = p1[1]-p0[1]
        d = p2[1]-p0[1]
        e = p[0]-p0[0]
        f = p[1]-p0[1]
        det = a*d-b*c
        if det == 0:
            return False
        else:
            x = (e*d-f*b)/det
            y = (a*f-c*e)/det
            return -0.01 <= x <= 1 and -0.01 <= y <= 1 and x + y <= 1

    # internal - find which robot legs are touching the floor and how is the body tilted
    def findZRxRyPlane(self,legs):
        lowestCombi = []
        for (legCombi, compLegCombi) in zip(self.legCombi, self.complementaryLegCombi):          # go through 3-legs combinations
            p0 = legs[legCombi[0]][3,:]
            p1 = legs[legCombi[1]][3,:]
            p2 = legs[legCombi[2]][3,:]
            if self.inTriangle(p0,p1,p2):       # inTrinagle = body center of gravity (point 0,0) is in trinagle -> stable combination of legs
                v0 = p1-p0
                v1 = p2-p0
                normal = np.cross(v0,v1)        # calculate normal vector of the plane given by 3 leg endpoints (feets)
                d = np.dot(normal,p0)                                                        
                for i in compLegCombi:                                  # go through all remaining legs and check if any is lower than this combination
                        dist = np.dot(normal,legs[i][3,:])
                        if dist < d:
                            break
                if dist >= d :                                      # if no other leg is lower than combination of these 3, you found it
                    lowestCombi = legCombi
                   
        v0 = legs[lowestCombi[1]][3,:]-legs[lowestCombi[0]][3,:]
        v1 = legs[lowestCombi[2]][3,:]-legs[lowestCombi[0]][3,:]
        normal = np.cross(v0,v1)                                    # once more calculate normal vector, now of the plane given by 3 lowest legs
        angleX = math.atan(normal[1]/normal[2])                     # get tilt of the body in Rx and Ry
        angleY = math.atan(-normal[0]/normal[2])
        zDist = np.dot(normal,legs[lowestCombi[0]][3,:])/np.sqrt(np.dot(normal,normal))     # get body height above the floor
        return zDist, angleX, angleY

    # internal - find how the robot moved in horizontal plane since the last situation
    def updateXYRzMotionVector(self,legs):
        xDist = 0
        yDist = 0
        angleZ = 0

        points = np.array(map(lambda leg: leg[3,:], legs))
        
        newContactB = (points < 2)[:,2]  # which legs are max 2mm above ground ~ is on the the ground

        counter = 0
        for i in range(6):
            if self.oldContactB[i] and newContactB[i]:  # leg was and still is on the ground, calculated displacement
                counter += 1
                [x,y] = (points[i,0:2] - self.oldContactP[i,0:2])   #difference between previous and new position)
                xDist -= x
                yDist -= y

                r = points[i,0:2]
                angleZ += math.atan(np.dot([r[1],-r[0]],[x,y])/np.dot(r,r))

        # body displacement = average displacement of all legs on the ground
        if counter > 0:
            xDist /= counter
            yDist /= counter
            angleZ /= counter

        # prevention of rounding errors - if the calculated displacement is less than 1 mm or 0.01 rad, say it was none 
        if np.abs(xDist) < 1:
            xDist = 0
        if np.abs(yDist) < 1:
            yDist = 0
        if np.abs(angleZ) < 0.01:
            angleZ = 0

        # the reference world displacement (x,y) is obtained from the robot local coordinated (xDist,yDist) rotated by the robot orientation
        x,y,t = self.RotZ([xDist,yDist,0], self.oldXYRzVector[2] + angleZ/2)
            
        self.oldXYRzVector += [x,y,angleZ]  # store actual robot position
        self.oldContactP = points
        self.oldContactB = newContactB
        return self.oldXYRzVector, (xDist, yDist, angleZ)
        
    def RotX(self,pos,angle):
        Rx = [[1,0,0],
              [0,math.cos(angle),-math.sin(angle)],
              [0,math.sin(angle),math.cos(angle)]]
        return np.dot(Rx,pos)

    def RotY(self,pos,angle):
        Ry = [[math.cos(angle),0,math.sin(angle)],
              [0,1,0],
              [-math.sin(angle),0,math.cos(angle)]]     
        return np.dot(Ry,pos) 

    def RotZ(self,pos,angle):
        Rz = [[math.cos(angle),-math.sin(angle),0],
              [math.sin(angle),math.cos(angle),0],
              [0,0,1]]
        return np.dot(Rz,pos)

    def RotXYZ(self,pos,a):
        Rxyz = [[math.cos(a[2])*math.cos(a[1]), math.cos(a[2])*math.sin(a[1])*math.sin(a[0])-math.sin(a[2])*math.cos(a[0]), math.cos(a[2])*math.sin(a[1])*math.cos(a[0])+math.sin(a[2])*math.sin(a[0])],
                [math.sin(a[2])*math.cos(a[1]), math.sin(a[2])*math.sin(a[1])*math.sin(a[0])+math.cos(a[2])*math.cos(a[0]), math.sin(a[2])*math.sin(a[1])*math.cos(a[0])-math.cos(a[2])*math.sin(a[0])],
                [-math.sin(a[1])              , math.cos(a[1])*math.sin(a[0])                                             , math.cos(a[1])*math.cos(a[0])]]
        return np.dot(Rxyz,pos)

    def RotZX(self, pos, a = [0,0]):
        Rzx = [[math.cos(a[1]),-math.sin(a[1])                             , 0],
              [math.cos(a[0])*math.sin(a[1]),math.cos(a[0])*math.cos(a[1]), -math.sin(a[0])],
              [math.sin(a[0])*math.sin(a[1]),math.sin(a[0])*math.cos(a[1]), math.cos(a[0])]]
        return np.dot(Rzx,pos)

    # internal - build body and perform rotation and translation 
    def buildBody(self, pos = [0,0,0], angle = [0,0,0]):
        body = pos + self.RotXYZ(self.body,angle).T        
        return body

    # internal - build one leg and perform rotation and translation 
    def leg(self, pos = [0,0,0], angle = [0,0,0], legAngle = 0, servoAngles = [0,0,0]):
        h = [self.hip,0,0]
        t = self.RotY([self.thigh,0,0], servoAngles[1])
        f = self.RotY([self.foot,0,0], servoAngles[1] + servoAngles[2])

        d = np.vstack((h,t,f))
        d = self.RotZ(d.T, legAngle + servoAngles[0])
        d = self.RotXYZ(d, angle).T
        
        knee = pos + d[0]
        ankle = knee + d[1]
        tip = ankle + d[2]

        return knee, ankle, tip

    # internal - build legs and perform rotation and translation
    def legs(self, body, angle = [0,0,0]):

        legs = []
        for i in range(6):
            # get actual servo angles
            servoAngles = [self.con.servos[self.Dict[i*3+0]].getPosDeg(),
                           self.con.servos[self.Dict[i*3+1]].getPosDeg()*self.sign[i],
                           ankleOffset - self.con.servos[self.Dict[i*3+2]].getPosDeg()*self.sign[i]]
            servoAngles = map(lambda x: math.radians(x), servoAngles)

            knee, ankle, tip = self.leg(body[i], angle, self.bodyAngles[i], servoAngles)
            leg = np.vstack((body[i], knee, ankle, tip))
            legs.append(leg)

        return legs   
        
    # internal - build head and perform rotation and translation
    def buildHead(self, pos = [0,0,0], angle = [0,0,0], servoAngle = 0):
        d = self.RotZ(self.head, servoAngle)
        d = self.RotXYZ(d, angle).T + pos
        head = np.vstack((pos, d))
        return head

    # internal - build whole body and perform rotation and translation
    def buildRobot(self, pos = [0,0,0], angle = [0,0,0], withHead = False):
    
        body = self.buildBody(pos, angle)
        legs = self.legs(body, angle)
        if withHead:
            neck = (body[0,:]+body[5,:])/2
            head = self.buildHead(neck, angle, self.con.servos[self.Dict[18]].getPosDeg()/180*np.pi)
            return body, legs, head
        else:
            return body, legs

    # internal - rotate the scene according to camera and transpofr it to 2D
    def Projection3Dto2D(self, data3D, angle = [0,0]):
        D = self.RotZX(data3D.T, angle)
        data2DX = self.cameraZoom*D[0]/(D[1]-2000)+372
        data2DY = self.cameraZoom*D[2]/(D[1]-2000)+300
        return data2DX, data2DY

    # internal - mouse event handling (for scene camera rotation)
    def MouseClick(self, event):
        self.mousePos = [event.x, event.y]

    def LeftClickMove(self, event):
        self.cameraAngle[0] = self.cameraAngleOld[0] + (self.mousePos[1] - event.y)/100.0
        self.cameraAngle[1] = self.cameraAngleOld[1] - (self.mousePos[0] - event.x)/100.0

    def LeftClickRelease(self, event):
        self.cameraAngleOld[0] = self.cameraAngle[0]
        self.cameraAngleOld[1] = self.cameraAngle[1]

    def RightClickMove(self, event):
        self.cameraZoom = self.cameraZoomOld + (self.mousePos[1] - event.y)*2

    def RightClickRelease(self, event):
        self.cameraZoomOld = self.cameraZoom

    # plot the virtual robot                     
    def plot(self, centerPlot):

        # first build the robot with intial position and orientation (0,0,0)
        body, legs = self.buildRobot()

        # find which legs are touching the ground and how is the robot tilted
        zDist, angleX, angleY = self.findZRxRyPlane(legs)
        
        # build the robot again, now at known height zDist and tilt angleX, angleY
        body, legs = self.buildRobot(pos = [0, 0, -zDist], angle = [angleX, angleY, 0])

        # if the robot should be kept in the middle of the plot, reset movement vector
        if self.oldCenterPlot and not(centerPlot):
            self.oldXYRzVector[0] = 0
            self.oldXYRzVector[1] = 0

        # find how the robot moved in horizontal plane since the last situation    
        (xDist,yDist,angleZ), (dX, dY, dR) = self.updateXYRzMotionVector(legs)
   
        if centerPlot:
            # build robot with known rotation and height, but centered in the plot
            body, legs, head = self.buildRobot(pos = [0, 0, -zDist], angle = [angleX, angleY, angleZ], withHead = True)
            xOff = -int(xDist)%50 - 200
            yOff = -int(yDist)%50 - 200
            # move the grid under the robot instead of robot
            for i in range(8):
                self.gridx[i*2:i*2+2] = [[xOff+i*50, -200, 0], [xOff+i*50, 200 ,0]]
                self.gridy[i*2:i*2+2] = [[-200, yOff+i*50, 0], [200, yOff+i*50 ,0]]
            
        else:
            # build robot with known position and rotation
            body, legs, head = self.buildRobot(pos = [xDist, yDist, -zDist], angle = [angleX, angleY, angleZ], withHead = True)
        
        # stack data to one array
        data3D = body
        for i in range(6):
            data3D = np.vstack((data3D,legs[i]))
        data3D = np.vstack((data3D, head, self.plane, self.gridx, self.gridy))
        # 3D to 2D transformation
        data2DX, data2DY = self.Projection3Dto2D(data3D, self.cameraAngle)
        
        # plot the robot - update plot data
        self.canvas.coords(self.bodyPlot,data2DX[0],data2DY[0],data2DX[1],data2DY[1],data2DX[2],data2DY[2],data2DX[3],data2DY[3],data2DX[4],data2DY[4],data2DX[5],data2DY[5])
        for i in range(6):
            self.canvas.coords(self.legPlots[i],data2DX[i*4+6],data2DY[i*4+6],data2DX[i*4+7],data2DY[i*4+7],data2DX[i*4+8],data2DY[i*4+8],data2DX[i*4+9],data2DY[i*4+9])
        i = 30
        self.canvas.coords(self.headPlot,data2DX[i],data2DY[i],data2DX[i+1],data2DY[i+1],data2DX[i+2],data2DY[i+2],data2DX[i+3],data2DY[i+3],data2DX[i+4],data2DY[i+4])
        i = 35
        self.canvas.coords(self.planePlot,data2DX[i],data2DY[i],data2DX[i+1],data2DY[i+1],data2DX[i+2],data2DY[i+2],data2DX[i+3],data2DY[i+3])
        for i in range(8):
            self.canvas.coords(self.gridxPlots[i],data2DX[i*2+39],data2DY[i*2+39],data2DX[i*2+40],data2DY[i*2+40])
            self.canvas.coords(self.gridyPlots[i],data2DX[i*2+55],data2DY[i*2+55],data2DX[i*2+56],data2DY[i*2+56])

        self.oldCenterPlot = centerPlot
        return (dX, dY, dR)

#########################################################################################################################
# create GUI for Drawing
# by Michal G., 22-06-2013
#########################################################################################################################
class groupDrawingControl:
    def __init__(self, frame, con, Dict, rowY = 0, colX = 0):
        self.frame = Frame(frame,width = 1000, height = 500)
        self.rowY = rowY
        self.colX = colX
        self.on = False                     
        self.iZ = IntVar(value = 50)
        self.pos = [0, 0, self.iZ.get() + 5]
        self.posOld = [0, 0, self.iZ.get() + 5]
        self.lastCursorX = 0
        self.lastCursorY = 0
        
        self.scaleZ = Scale(self.frame, from_= 100, to = 35, length = 300, showvalue = 0, var = self.iZ, command = self.calibrateHeight)
        self.scaleZ.grid(row = 2, column = 1, rowspan = 3, sticky = S)
        Label(self.frame, textvariable = self.iZ, width = 3, font=('Tahoma', 10,'bold')).grid(row = 3, column = 0)
        Label(self.frame, text = 'Pen height', font=('Tahoma', 10,'bold')).grid(row = 1, column = 0, columnspan = 2, sticky = S)

        self.canvas = Canvas(self.frame, width = 500, height = 500, cursor = 'crosshair', bg = 'white')
        self.canvas.create_rectangle(3,3,501,501, width = 2, outline = 'black')
        self.canvas.bind("<Motion>", self.MoveCursor)
        self.canvas.bind("<B1-Motion>", self.LeftClickMove)
        self.canvas.bind("<Button-1>", self.LeftClick)
        self.canvas.bind("<ButtonRelease-1>", self.LeftClickRelease)
        self.canvas.grid(row = 0, column = 2, rowspan = 5)

        Button(self.frame, text = 'Clear canvas', width = 15, command = self.ClearCanvas).grid(row = 8, column = 2)
        
        self.Robot = kinematicRobot(con, Dict)

    def Loop(self):
        if self.on:
            # if the cursor position changed, update robot
            if  (self.pos != self.posOld):
                self.Robot.updateRobot(self.pos)

            self.posOld[0:3] = self.pos[0:3]

    def MoveCursor(self, event):
        self.pos[0] = (250 - event.y)/8.0
        self.pos[1] = (250 - event.x)/8.0
     
    def LeftClick(self, event):
        self.canvas.configure(cursor = 'target')
        self.lastCursorX = event.x
        self.lastCursorY = event.y
        self.pos[2] = self.iZ.get() # pen down

    def LeftClickMove(self, event):
        self.pos[0] = (250 - event.y)/8.0
        self.pos[1] = (250 - event.x)/8.0
        self.canvas.create_line((self.lastCursorX, self.lastCursorY, event.x, event.y), width = 2)
        self.lastCursorX = event.x
        self.lastCursorY = event.y

    def LeftClickRelease(self, event):
        self.canvas.configure(cursor = 'crosshair')
        self.pos[2] = self.iZ.get() + 5  # pen up

    def ClearCanvas(self):
        self.canvas.delete('all')
        self.canvas.create_rectangle(3,3,501,501, width = 2, outline = 'black')

    def calibrateHeight(self, event):
        self.pos[2] = self.iZ.get() + 5  # pen up

    def show(self):
        self.frame.grid(row = self.rowY, column = self.colX, rowspan = 100, columnspan = 100, sticky = N+W)
        self.Robot.initRobot(self.pos[2])
        self.on = True
        
    def hide(self):
        self.frame.grid_forget()
        self.on = False
                

#########################################################################################################################
# create GUI for Dancing
# by Michal G., 07-07-2013
#########################################################################################################################

## one dance move object
## ID - unique identifier. Moves can have the same name, but ID will be always different
## step - one item of steps. One defined robot position and orientation +  possible manual servo positions (or walk)
##        one dance move usually consists of at least 2 steps (2 robot positions)
## type: 'Single','Double','Pulse' - how fast will the steps be executed based on the detected music tempo (rythm). Double = 2x that fast
## music: 'Slow','Fast','No beat' - for what music speed is the move allowed to be execuded
class danceMove(object):
    def __init__(self, ID, name = 'New move', steps = [['no walk',[0,0,70,0,0,0],0],['no walk',[0,0,80,0,0,0],0]], type = ('Single','Double','Pulse'), music = ('Slow','Fast','No beat')):
        self.ID = ID
        self.name = name
        self.steps = steps
        self.length = len(steps)
        self.type = type
        self.music = music

    def getStep(self, step = 0):
        if step >= self.length:
            step = self.length - 1
        return self.steps[step]

    def canType(self, pattern):
        if pattern in self.type:
            return True
        else:
            return False

    def canMusic(self, speed):
        if speed in self.music:
            return True
        else:
            return False
####################################################################################################################################################################################
## Pop-up dialog for creating or editing one dance step (or 2 for walk action)
class dialogDanceStep(object):
    def __init__(self, parent, servoDict, data_in = []):
        self.parent = parent
        self.modalPane = Toplevel(self.parent)
        self.modalPane.transient(self.parent)
        self.modalPane.grab_set()

        self.modalPane.title("One dance step")
        self.modalPane.geometry("+400+200")
        self.modalPane.bind("<Return>", self._OK)
        self.modalPane.bind("<Escape>", self._cancel)
        Button(self.modalPane, text = "OK", width = 12, height = 2, command = self._OK).grid(row = 3, column = 2, sticky = SE)
        Label(self.modalPane, text="\t").grid(row = 3, column = 3)
        Button(self.modalPane, text = "Cancel", width = 12, height = 2, command = self._cancel).grid(row = 3, column = 4, sticky = SW)

        self.servoDict = servoDict
        self.servoOList = ("LF hip", "LF knee", "LF ankle", "LM hip", "LM knee", "LM ankle", "LB hip", "LB knee", "LB ankle", "RF hip", 
                           "RF knee", "RF ankle", "RM hip", "RM knee", "RM ankle", "RB hip", "RB knee", "RB ankle", "Head")
        if data_in == []:
            pV = ((0,0,70,0,0,0),(0,0,70,0,0,0))
            dpV = ((0,0,0),(0,0,0))
            walk = 0
            servos = 0
            servo = ("LF hip","LF hip","LF hip","LF hip","LF hip","LF hip")
            servoAngle = (0,0,0,0,0,0)
            servoMotion = ('Relative','Relative','Relative','Relative','Relative','Relative')
        else:
            if data_in[0] == 'walk':
                steps = data_in[1:3]
                pV = [steps[0][0],steps[1][0]]
                dpV = [steps[0][1],steps[1][1]]
                walk = 1
                servos = 0
                servo = ("LF hip","LF hip","LF hip","LF hip","LF hip","LF hip")
                servoAngle = (0,0,0,0,0,0)
                servoMotion = ('Relative','Relative','Relative','Relative','Relative','Relative')
            else:
                step = data_in[1]
                pV = [step[0],step[0]]
                dpV = ((0,0,0),(0,0,0))
                walk = 0
                servos = step[1]
                servo = []
                servoAngle = []
                servoMotion = []
                for j in range(servos):
                    servo.append(self.servoOList[servoDict.index(step[2+j][0])])
                    servoAngle.append(step[2+j][1])
                    if step[2+j][2] == 'R':
                        servoMotion.append('Relative')
                    else:
                        servoMotion.append('Absolute')
                for j in range(servos,6):
                    servo.append("LF hip")
                    servoAngle.append(0)
                    servoMotion.append('Relative')
   
        self.addSpace((3,3))
        ##################
        self.posFrame = LabelFrame(self.modalPane, text = 'Robot position:')
        self.posFrame.grid(row = 1, column = 1, sticky = W)

        self.posOList = []
        self.posOList.append(range(-20,21,2))
        self.posOList.append(range(-20,21,2))
        self.posOList.append(range(50,91,5))
        self.posOList.append(range(-10,11))
        self.posOList.append(range(-10,11))
        self.posOList.append(range(-10,11))

        Label(self.posFrame, text = '1:').grid(row = 2, column = 0)
        self.posLabel2 = Label(self.posFrame, text = '2:')
        self.posLabel2.grid(row = 3, column = 0)
        self.posLabel2.config(state = 'disabled')
        Label(self.posFrame, text = 'X:').grid(row = 1, column = 1)
        Label(self.posFrame, text = 'Y:').grid(row = 1, column = 2)
        Label(self.posFrame, text = 'Z:').grid(row = 1, column = 3)
        Label(self.posFrame, text = 'Rx:').grid(row = 1, column = 4)
        Label(self.posFrame, text = 'Ry:').grid(row = 1, column = 5)
        Label(self.posFrame, text = 'Rz:').grid(row = 1, column = 6)      

        self.posVar = []
        self.posOm = []
        for i in range(2):
            posVar = []
            om = []
            for j in range(6):
                posVar.append(IntVar(value = pV[i][j]))
                posOm = OptionMenu(self.posFrame, posVar[j], *self.posOList[j])
                posOm.grid(row = i + 2, column = j + 1, sticky = E)
                if i < 1 or walk:
                    posOm.config(width = 2)
                else:
                    posOm.config(width = 2, state = 'disabled')
                om.append(posOm)
            self.posVar.append(posVar)
            self.posOm.append(om)
            
        Label(self.posFrame, text="\t").grid(row = 4, column = 8)

        ##################
        self.addSpace((2, 0))
        self.walkFrame = LabelFrame(self.modalPane, text = 'Robot walk:')
        self.walkFrame.grid(row = 1, column = 2, columnspan = 4, sticky = W)
        
        self.walk = IntVar(value = walk)
        self.walkCButton = Checkbutton(self.walkFrame, text = 'walk', variable = self.walk, command = self.changeWalkCB)
        self.walkCButton.grid(row = 1, column = 0, rowspan = 2)
        self.walkLabeldX = Label(self.walkFrame, text = 'dX:')
        self.walkLabeldY = Label(self.walkFrame, text = 'dY:')
        self.walkLabeldRz = Label(self.walkFrame, text = 'dRz:')
        self.walkLabeldX.grid(row = 0, column = 1)
        self.walkLabeldY.grid(row = 0, column = 2)
        self.walkLabeldRz.grid(row = 0, column = 3)
        if not walk:
            self.walkLabeldX.config(state = 'disabled')
            self.walkLabeldY.config(state = 'disabled')
            self.walkLabeldRz.config(state = 'disabled')

        self.dPosOList = []
        self.dPosOList.append(range(-15,16,3))
        self.dPosOList.append(range(-15,16,3))
        self.dPosOList.append(range(-15,16,3))
        self.dPosVar = []
        self.dPosOm = []
        for i in range(2):
            dPosVar = []
            om = []
            for j in range(3):
                dPosVar.append(IntVar(value = dpV[i][j]))
                dPosOm = OptionMenu(self.walkFrame, dPosVar[j], *self.dPosOList[j])
                dPosOm.grid(row = i + 1, column = j + 1, sticky = E)
                if walk:
                    dPosOm.config(width = 2)
                else:
                    dPosOm.config(width = 2, state = 'disabled')
                om.append(dPosOm)
            self.dPosVar.append(dPosVar)
            self.dPosOm.append(om)

        Label(self.walkFrame, text="\t").grid(row = 4, column = 4)
        
        ##################
        self.addSpace((0, 2))
        self.servoFrame = LabelFrame(self.modalPane, text = ' Add manual servo control:')
        self.servoFrame.grid(row = 3, column = 1, sticky = W)
        
        self.servosLabel = Label(self.servoFrame, text = 'Nr of servos used:')
        self.servosLabel.grid(row = 0, column = 1, columnspan = 2, sticky = E)
        self.servosVar = IntVar(value = servos)
        self.servosVar.trace('w', self.changeServoNr)
        self.servosOList = range(7)
        self.servosOm = OptionMenu(self.servoFrame, self.servosVar, *self.servosOList)
        self.servosOm.grid(row = 0, column = 3, sticky = W)

        Label(self.servoFrame, text="\t\t").grid(row = 1, column = 0)
        self.servoLabel1 = Label(self.servoFrame, text="Servos:")
        self.servoLabel1.grid(row = 1, column = 1)
        self.servoLabel2 = Label(self.servoFrame, text="Angle:")
        self.servoLabel2.grid(row = 1, column = 2)
        self.servoLabel3 = Label(self.servoFrame, text="Movement:")
        self.servoLabel3.grid(row = 1, column = 3)
        Label(self.servoFrame, text="\t").grid(row = 9, column = 4)

        if walk:
            self.servosLabel.config(state = 'disabled')
            self.servoLabel1.config(state = 'disabled')
            self.servoLabel2.config(state = 'disabled')
            self.servoLabel3.config(state = 'disabled')
            self.servosOm.config(state = 'disabled')
        
        self.servoLabels = []
        
        self.servoVar = []
        self.servoOm = []
        self.servoAngleOList = range(-80,81,5)
        self.servoAngleVar = []
        self.servoAngleOm = []
        self.servoMotionOList = ("Relative","Absolute")
        self.servoMotionVar = []
        self.servoMotionOm = []   
        
        for j in range(6): 
            label = Label(self.servoFrame, text = ('Servo %d:' % (j+1)))
            label.grid(row = j + 2, column = 0)
            self.servoLabels.append(label)

            self.servoVar.append(StringVar(value = servo[j]))
            self.servoAngleVar.append(IntVar(value = servoAngle[j]))
            self.servoMotionVar.append(StringVar(value = servoMotion[j]))
            om1 = OptionMenu(self.servoFrame, self.servoVar[j], *self.servoOList)
            om2 = OptionMenu(self.servoFrame, self.servoAngleVar[j], *self.servoAngleOList)
            om3 = OptionMenu(self.servoFrame, self.servoMotionVar[j], *self.servoMotionOList)
            if j < servos:
                om1.config(width = 8)
                om2.config(width = 2)
                om3.config(width = 8)
            else:
                label.config(state = 'disabled')
                om1.config(width = 8, state = 'disabled')
                om2.config(width = 2, state = 'disabled')
                om3.config(width = 8, state = 'disabled')
                
            om1.grid(row = j + 2, column = 1)
            om2.grid(row = j + 2, column = 2)
            om3.grid(row = j + 2, column = 3)
            self.servoOm.append(om1)
            self.servoAngleOm.append(om2)
            self.servoMotionOm.append(om3)
            
        self.addSpace((6, 4))
     
    def addSpace(self, coords):
        Label(self.modalPane, text="\t\t").grid(row=coords[1], column=coords[0])
        
    def changeWalkCB(self): 
        if self.walk.get():
            self.posLabel2.config(state = 'active')
            self.walkLabeldX.config(state = 'active')
            self.walkLabeldY.config(state = 'active')
            self.walkLabeldRz.config(state = 'active')
            for j in range(6):
                self.posOm[1][j].config(state = 'active')
            for i in range(2):
                for j in range(3):
                    self.dPosOm[i][j].config(state = 'active')
                    
            self.servosLabel.config(state = 'disabled')
            self.servoLabel1.config(state = 'disabled')
            self.servoLabel2.config(state = 'disabled')
            self.servoLabel3.config(state = 'disabled')
            self.servosOm.config(state = 'disabled')
            for j in range(6):
                self.servoLabels[j].config(state = 'disabled')
                self.servoOm[j].config(state = 'disabled')
                self.servoAngleOm[j].config(state = 'disabled')
                self.servoMotionOm[j].config(state = 'disabled')              
        else:
            self.posLabel2.config(state = 'disabled')
            self.walkLabeldX.config(state = 'disabled')
            self.walkLabeldY.config(state = 'disabled')
            self.walkLabeldRz.config(state = 'disabled')
            for j in range(6):
                self.posOm[1][j].config(state = 'disabled')
            for i in range(2):
                for j in range(3):
                    self.dPosOm[i][j].config(state = 'disabled')

            self.servosLabel.config(state = 'active')
            self.servoLabel1.config(state = 'active')
            self.servoLabel2.config(state = 'active')
            self.servoLabel3.config(state = 'active')
            self.servosOm.config(state = 'active')
            for j in range(self.servosVar.get()):
                self.servoLabels[j].config(state = 'active')
                self.servoOm[j].config(state = 'active')
                self.servoAngleOm[j].config(state = 'active')
                self.servoMotionOm[j].config(state = 'active')

    def changeServoNr(self, event, temp, temp2):        
        for j in range(self.servosVar.get()):
            self.servoLabels[j].config(state = 'active')
            self.servoOm[j].config(state = 'active')
            self.servoAngleOm[j].config(state = 'active')
            self.servoMotionOm[j].config(state = 'active')
        for j in range(self.servosVar.get(),6):
            self.servoLabels[j].config(state = 'disabled')
            self.servoOm[j].config(state = 'disabled')
            self.servoAngleOm[j].config(state = 'disabled')
            self.servoMotionOm[j].config(state = 'disabled')
      

    def _OK(self, event=None):
        self.modalPane.destroy()
        steps = []
        if self.walk.get():
            steps.append('walk')
            for i in range(2):
                step = []
                pos = []
                for j in range(6):
                    pos.append(self.posVar[i][j].get())
                dPos = []
                for j in range(3):
                    dPos.append(self.dPosVar[i][j].get())
                step.append(pos)
                step.append(dPos)
                steps.append(step)
        else:
            steps.append('no walk')
            step = []
            pos = []
            for j in range(6):
                pos.append(self.posVar[0][j].get())
            step.append(pos)
            step.append(self.servosVar.get())
            for j in range(self.servosVar.get()):
                servo = []
                servo.append(self.servoDict[self.servoOList.index(self.servoVar[j].get())])
                servo.append(self.servoAngleVar[j].get())
                servo.append(self.servoMotionVar[j].get()[0])
                step.append(servo)
            steps.append(step)
        self.steps = steps

    def _cancel(self, event=None):
        self.steps = []
        self.modalPane.destroy()

    def returnValue(self):
        self.parent.wait_window(self.modalPane)
        return self.steps
        
######################################################################################################################################################################################
## Frame for creating or editing one Dance move
## Shows only when a move is created or edited
class frameOneMove:
    def __init__(self, master, movesSelf, servoDict, row = 2, column = 0):
        self.master = master
        self.frame = LabelFrame(self.master, text = 'One dance move:')
        self.row = row
        self.column = column
        self.movesSelf = movesSelf

        self.stepList = []

        self.servoDict = servoDict
        self.nameDict = ["LFH", "LFK", "LFA", "LMH", "LMK", "LMA", "LBH", "LBK", "LBA", "RFH", "RFK", "RFA", "RMH", "RMK", "RMA", "RBH", "RBK", "RBA", "HED"]

        self.testIndex = 0

        self.sID = StringVar(value = '0001')

        Label(self.frame, text = '\tName:').grid(row = 0, column = 0, sticky = E)
        self.nameEntry = Entry(self.frame, width = 40)
        self.nameEntry.insert(0,'New move')
        self.nameEntry.grid(row = 0, column = 1, columnspan = 3, sticky = W)
        
        Label(self.frame, text = '\tMove ID:').grid(row = 0, column = 5, sticky = E)
        Label(self.frame, textvar = self.sID, width = 7, relief = 'sunken').grid(row = 0, column = 6, sticky = W)

        #### Steps frame #####
        self.stepsFrame = LabelFrame(self.frame, text = 'Steps:')
        self.stepsFrame.grid(row = 3, column = 0, columnspan = 10, sticky = W)

        Label(self.stepsFrame, text="Step        Position          + Walk        or        + Manual servo moves", font = ("Courier", 9)).grid(row = 3, column = 1, sticky = W)
        Label(self.stepsFrame, text=" Nr  X   Y   Z  Rx  Ry  Rz  dX  dY  dRz Servo 1  Servo 2  Servo 3  Servo 4  Servo 5  Servo 6 ", font = ("Courier", 9)).grid(row = 4, column = 1, sticky = W)

        self.stepsListFrame = Frame(self.stepsFrame)
        self.stepsListFrame.grid(row = 5, column = 1, rowspan = 5)
        scrollBar = Scrollbar(self.stepsListFrame)
        scrollBar.grid(row = 0, column = 3, sticky = N+S)
        self.stepListBox = Listbox(self.stepsListFrame, width = 93, height = 6, selectmode = SINGLE, activestyle = NONE, font = ("Courier", 9))
        self.stepListBox.grid(row = 0, column = 0)
        scrollBar.config(command = self.stepListBox.yview)
        self.stepListBox.config(yscrollcommand = scrollBar.set)

        Label(self.stepsFrame, text="\t").grid(row = 5, column = 2)
        Button(self.stepsFrame, text = 'Add', command = self.addStep, width = 8).grid(row = 5, column = 3)
        Button(self.stepsFrame, text = 'Insert', command = self.insertStep, width = 8).grid(row = 6, column = 3)
        Button(self.stepsFrame, text = 'Edit', command = self.editStep, width = 8).grid(row = 7, column = 3)
        Button(self.stepsFrame, text = 'Delete', command = self.deleteStep, width = 8).grid(row = 8, column = 3)

        #### Move types frame #####
        self.moveTypesFrame = LabelFrame(self.frame, text = 'Move types:')
        self.moveTypesFrame.grid(row = 4, column = 0, columnspan = 3, sticky = W)

        Label(self.moveTypesFrame, text = '\tBeat:').grid(row = 0, column = 0)
        self.moveTypeSingle = IntVar(value = 1)
        Checkbutton(self.moveTypesFrame, text = 'Single:', width = 10, anchor = W, var = self.moveTypeSingle, command = self.changeMoveTypes).grid(row = 1, column = 0)
        self.moveTypeDouble = IntVar(value = 1)
        Checkbutton(self.moveTypesFrame, text = 'Double:', width = 10, anchor = W, var = self.moveTypeDouble, command = self.changeMoveTypes).grid(row = 2, column = 0)
        self.moveTypePulse = IntVar(value = 1)
        Checkbutton(self.moveTypesFrame, text = 'Pulse:', width = 10, anchor = W, var = self.moveTypePulse, command = self.changeMoveTypes).grid(row = 3, column = 0)

        self.moveTypeExampleSingle = StringVar(value = '1   2   1   2')
        self.moveTypeExampleDouble = StringVar(value = '1 2 1 2 1 2 1 2')
        self.moveTypeExamplePulse =  StringVar(value = '12  12  12  12')
        Label(self.moveTypesFrame, text = '*   *   *   *', justify = LEFT, font = ("Courier", 11)).grid(row = 0, column = 1, sticky = W)
        Label(self.moveTypesFrame, textvar = self.moveTypeExampleSingle, width = 15, anchor = W, font = ("Courier", 11)).grid(row = 1, column = 1, sticky = W)
        Label(self.moveTypesFrame, textvar = self.moveTypeExampleDouble, width = 15, anchor = W, font = ("Courier", 11)).grid(row = 2, column = 1, sticky = W)
        Label(self.moveTypesFrame, textvar = self.moveTypeExamplePulse, width = 15, anchor = W, font = ("Courier", 11)).grid(row = 3, column = 1, sticky = W)

        #### Music frame #####
        self.musicFrame = LabelFrame(self.frame, text = 'Music:')
        self.musicFrame.grid(row = 4, column = 3, columnspan = 1, sticky = W+N+S)

        self.musicSlow = IntVar(value = 1)
        Checkbutton(self.musicFrame, text = 'Slow (< 120 BPM)', var = self.musicSlow).grid(row = 0, column = 0, sticky = W)
        self.musicFast = IntVar(value = 1)
        Checkbutton(self.musicFrame, text = 'Fast (> 120 BPM)', var = self.musicFast).grid(row = 1, column = 0, sticky = W)
        self.musicNoBeat = IntVar(value = 0)
        Checkbutton(self.musicFrame, text = 'No beat (0 BPM)', var = self.musicNoBeat).grid(row = 2, column = 0, sticky = W)

        #### Standard buttons #####
        self.buttonFrame = Frame(self.frame)
        self.buttonFrame.grid(row = 4, column = 4, columnspan = 10)

        Label(self.buttonFrame, text="\t").grid(row = 0, column = 2)
        Label(self.buttonFrame, text="\t").grid(row = 0, column = 4)
        Button(self.buttonFrame, text = 'Test', command = self._Test, width = 15, height = 2).grid(row = 0, column = 1)
        Button(self.buttonFrame, text = 'OK', command = self._OK, width = 15, height = 2).grid(row = 0, column = 3)
        Button(self.buttonFrame, text = 'Cancel', command = self._Cancel, width = 15, height = 2).grid(row = 0, column = 5)
         
    def addStep(self):
        out = dialogDanceStep(self.frame, self.servoDict).returnValue()  # show the pop-up dialog window
        if out == []:
            pass  # action cancelled
        else:
            if out[0] == 'walk':        # walk is always 2 steps
                self.stepList.append([out[0],out[1]])
                self.stepList.append([out[0],out[2]])
            else:
                self.stepList.append(out)
                
            self.refreshStepListBox()
            self.changeMoveTypes()
            self.stepListBox.selection_set(END)
            self.stepListBox.see(END)

    def insertStep(self):
        try:
            index = int(self.stepListBox.curselection()[0])
            if self.stepList[index][0] == 'walk':  # walk is always 2 steps, find which one is the second step
                prevWalkIndex = index
                while prevWalkIndex >= 0 and self.stepList[prevWalkIndex][0] == 'walk': 
                    prevWalkIndex -= 1
                prevWalkIndex += 1
                if prevWalkIndex % 2 != index % 2:  # they are two or 4 steps appart, take the next one
                    index -= 1
                
            out = dialogDanceStep(self.frame, self.servoDict).returnValue()  # show the pop-up dialog window
            if out == []:
                pass  # action cancelled
            else:
                # insert
                if out[0] == 'walk':
                    self.stepList.insert(index, [out[0],out[1]])
                    self.stepList.insert(index+1, [out[0],out[2]])
                else:
                    self.stepList.insert(index, out)

                self.refreshStepListBox()
                self.changeMoveTypes()
            self.stepListBox.selection_set(index)
            self.stepListBox.see(index)
        except IndexError:
            self.addStep()

    def editStep(self):
        try:
            index = int(self.stepListBox.curselection()[0])
            if self.stepList[index][0] == 'walk':  # walk is always 2 steps, find which one is the second step
                prevWalkIndex = index
                while prevWalkIndex >= 0 and self.stepList[prevWalkIndex][0] == 'walk': 
                    prevWalkIndex -= 1
                prevWalkIndex += 1
                if prevWalkIndex % 2 != index % 2:
                    index -= 1
                data_in = [self.stepList[index][0],self.stepList[index][1],self.stepList[index+1][1]]
            else:
                data_in = self.stepList[index]
                
            out = dialogDanceStep(self.frame, self.servoDict, data_in).returnValue()  # show the pop-up dialog window
            
            if out == []:
                pass  # action cancelled
            else:
                # delete list item
                if self.stepList[index][0] == 'walk':
                    del self.stepList[index:index+2]
                else:
                    del self.stepList[index]
                # replace with new
                if out[0] == 'walk':
                    self.stepList.insert(index, [out[0],out[1]])
                    self.stepList.insert(index+1, [out[0],out[2]])
                else:
                    self.stepList.insert(index, out)

                self.refreshStepListBox()
                self.changeMoveTypes()
            self.stepListBox.selection_set(index)
            self.stepListBox.see(index)
        except IndexError:  # nothing was selected
            pass

    def deleteStep(self):
        try:
            index = int(self.stepListBox.curselection()[0])
            if self.stepList[index][0] == 'walk':  # walk is always 2 steps, find which one is the second step
                if index + 1 == len(self.stepList):  # the last item in the list
                    del self.stepList[index-1:index+1]
                elif self.stepList[index+1][0]  == 'walk':
                    del self.stepList[index:index+2]
                else:
                    del self.stepList[index-1:index+1]
            else:
                del self.stepList[index]

            self.refreshStepListBox()
            self.changeMoveTypes()
        except IndexError:
            pass

    # shows example of how the steps will be executed with the music tempo
    def changeMoveTypes(self, event = []):
        steps = len(self.stepList)
        if steps:
            if self.moveTypeSingle.get():
                self.moveTypeExampleSingle.set("%d   %d   %d   %d" % (0%steps+1, 1%steps+1, 2%steps+1, 3%steps+1))
            else:
                self.moveTypeExampleSingle.set("")
                
            if self.moveTypeDouble.get():
                self.moveTypeExampleDouble.set("%d %d %d %d %d %d %d %d" % (0%steps+1, 1%steps+1, 2%steps+1, 3%steps+1, 4%steps+1, 5%steps+1, 6%steps+1, 7%steps+1))
            else:
                self.moveTypeExampleDouble.set("")
                
            if self.moveTypePulse.get():
                self.moveTypeExamplePulse.set("%d%d  %d%d  %d%d  %d%d" % (0%steps+1, 1%steps+1, 2%steps+1, 3%steps+1, 4%steps+1, 5%steps+1, 6%steps+1, 7%steps+1))
            else:
                self.moveTypeExamplePulse.set("")
                
    def refreshStepListBox(self):
        self.stepListBox.delete(0,END)
        for i in range(len(self.stepList)):
            step = self.stepList[i]
            s = "%2d #" % (i+1)
            s += "%3d|%3d|%3d|%3d|%3d|%3d#" % tuple(step[1][0])
            if step[0] == 'walk':
                s += "%3d|%3d|%3d#" % tuple(step[1][1])
            else:
                s += "           #"
                for i in range(step[1][1]):
                    s += '%s=%3d%s|' % (self.nameDict[self.servoDict.index(step[1][i+2][0])],step[1][i+2][1],step[1][i+2][2])
            self.stepListBox.insert(END,s)

    # shows the whole frame (defaultly is hidden)
    def show(self, moveList, index, lastMoveID, title = 'One move:'):
        self.frame.config(text = title)
        self.moveList = moveList        # list of all moves
        self.lastMoveID = lastMoveID    
        self.moveListIndex = index
        
        if index >= len(self.moveList):   #create new move
            self.sID.set("%04d" % (lastMoveID + 1))    # ID is always incremented regardless of deleting any move. To keep consistency of saved sequences of moves
            self.nameEntry.delete(0,END)
            self.nameEntry.insert(0,'New move')
            self.stepListBox.delete(0,END)
            self.stepList = []
            self.moveTypeSingle.set(1)
            self.moveTypeDouble.set(1)
            self.moveTypePulse.set(0)
            self.musicSlow.set(1)
            self.musicFast.set(1)
            self.musicNoBeat.set(1)
        else:                           # edit move
            dM = moveList[index]
            self.sID.set("%04d" % dM.ID)
            self.nameEntry.delete(0,END)
            self.nameEntry.insert(0,dM.name)
            self.stepListBox.delete(0,END)
            self.stepList = []
            for i in range(dM.length):
                self.stepList.append(dM.getStep(i))
            self.moveTypeSingle.set(dM.canType('Single'))
            self.moveTypeDouble.set(dM.canType('Double'))
            self.moveTypePulse.set(dM.canType('Pulse'))
            self.musicSlow.set(dM.canMusic('Slow'))
            self.musicFast.set(dM.canMusic('Fast'))
            self.musicNoBeat.set(dM.canMusic('No beat'))

            self.refreshStepListBox()
            self.changeMoveTypes()
       
        self.frame.grid(row = self.row, column = self.column)

    def testSteps(self):
        if self.testIndex < len(self.stepList):
            self.stepListBox.selection_clear(0,END)
            self.stepListBox.selection_set(self.testIndex)
            self.stepListBox.see(self.testIndex)
            step = self.stepList[self.testIndex]
            if (step[0] == 'walk'):
                self.movesSelf.Robot.updateRobot(pos = step[1][0][0:3], angle = step[1][0][3:6], move = True, dPos = step[1][1], send = False)
            else:
                self.movesSelf.Robot.updateRobot(pos = step[1][0][0:3], angle = step[1][0][3:6], move = False, send = False)            
                # if there are manual servo values, update them as well
                servoNr = step[1][1]
                for i in range(servoNr):
                    [servo, angle, move] = step[1][2+i]
                    if move == 'R':
                        angle += self.movesSelf.con.servos[servo].getPosDeg()
                    angle = min(max(angle, -80), 80)
                    self.movesSelf.con.servos[servo].setPos(deg = angle, move = False)
                    
            self.testIndex += 1
            self.master.after(1000, self.testSteps)
        else:
            self.testIndex = 0
            self.movesSelf.test = False

    def _Test(self):
        if len(self.stepList):
            self.movesSelf.test = True
            self.testIndex = 0
            self.testSteps()
        
    # save changes or new move
    def _OK(self):
        type = []
        if self.moveTypeSingle.get():
            type.append('Single')
        if self.moveTypeDouble.get():
            type.append('Double')
        if self.moveTypePulse.get():
            type.append('Pulse')
            
        music = []
        if self.musicSlow.get():
            music.append('Slow')
        if self.musicFast.get():
            music.append('Fast')
        if self.musicNoBeat.get():
            music.append('No beat')
            
        dM = danceMove(ID = int(self.sID.get()),name = self.nameEntry.get(), steps = self.stepList, type = type, music = music)
        if self.lastMoveID < int(self.sID.get()):  # new move
            self.moveList.append(dM)
        else:                                      # edited move
            self.moveList[self.moveListIndex] = dM

        self.frame.grid_forget()
        self.movesSelf.refreshMoveListBox(index = self.moveListIndex)
        self.movesSelf.lastMoveID = max(int(self.sID.get()), self.lastMoveID)
        self.movesSelf.autoSaveMoves()
        self.movesSelf.createMoveButton.config(state = 'active')
        self.movesSelf.editMoveButton.config(state = 'active')
        self.movesSelf.deleteMoveButton.config(state = 'active')
        self.movesSelf.importMoveButton.config(state = 'active')
        self.movesSelf.exportMoveButton.config(state = 'active')
        self.movesSelf.startDanceButton.config(state = 'active')

    # cancel any changes
    def _Cancel(self):
        self.frame.grid_forget()
        self.movesSelf.refreshMoveListBox(index = self.moveListIndex)
        self.movesSelf.createMoveButton.config(state = 'active')
        self.movesSelf.editMoveButton.config(state = 'active')
        self.movesSelf.deleteMoveButton.config(state = 'active')
        self.movesSelf.importMoveButton.config(state = 'active')
        self.movesSelf.exportMoveButton.config(state = 'active')
        self.movesSelf.startDanceButton.config(state = 'active')
        

######################################################################################################################################################################################
class groupDancingControl:
    def __init__(self, frame, con, Dict, rowY = 0, colX = 0):
        self.frame = Frame(frame,width = 1000, height = 500)
        self.con = con
        self.servoDict = []
        for i in range(len(Dict)):
            self.servoDict.append(Dict[i][1])
        self.rowY = rowY
        self.colX = colX
        self.on = False
        self.test = False

        self.countB = 0         # counter from the last detected beat [int]
        self.countB_hist = []   # history of the time-spacing of the the last 4 beats (3 spaces) [list of int]
        self.tempo = 0          # detected tempo length [float, in cycles]
        self.countT = 0         # counter from the last tempo pulse [float], for precise tempo keeping)
        self.countM = 0         # counter from the last tempo pulse [int], for Move execution)
        self.countNB = 0        # counter of the No-beat mode [int]
        self.countS = 0         # silence counter [int] for reseting tempo 
        self.max_energy = 0     # maximum detected audio signal energy
        ##################################################################################################
        self.chuck = 2048       # audio data chuck per 1 cycle, 1 cycle time = self.chuck/44100 [s]
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format = pyaudio.paInt16, channels = 1, rate = 44100, input = True, frames_per_buffer = self.chuck)
        ##################################################################################################
        self.Robot = kinematicRobot(con, Dict)  #inverse kinematic robot instance
        
        ## Top Frame #####################################################################################
        self.topFrame = Frame(self.frame)#, bg = 'blue')
        self.topFrame.grid(row = 0, column = 0, sticky = E+W+N)
     
        Label(self.topFrame, text = '  ').grid(row = 1, column = 0)
        self.startDanceButton = Button(self.topFrame, text = 'Start', width = 10,  font=('Tahoma', 10,'bold'), command = self.startDance)
        self.startDanceButton.grid(row = 1, column = 1)
        Label(self.topFrame, text = '  ').grid(row = 1, column = 2)
        Button(self.topFrame, text = 'Pause', width = 10,  font=('Tahoma', 10,'bold'), command = self.pauseDance).grid(row = 1, column = 3)
        Label(self.topFrame, text = '  ').grid(row = 1, column = 4)
        Button(self.topFrame, text = 'Stop', width = 10, font=('Tahoma', 10,'bold'), command = self.stopDance).grid(row = 1, column = 5)
        Label(self.topFrame, text = '  ').grid(row = 1, column = 6)

        self.whichList = IntVar()
        Radiobutton(self.topFrame, text = "Sequence", variable = self.whichList, value = 0).grid(row = 2, column = 1, sticky = W)
        Radiobutton(self.topFrame, text = "All moves", variable = self.whichList, value = 1).grid(row = 2, column = 3, sticky = W)
        self.randomVar = IntVar()
        Checkbutton(self.topFrame, text = 'Random order', var = self.randomVar, command = self.setBPM).grid(row = 2, column = 5, sticky = W)

        self.danceIndicatorVar = StringVar(value = 'Stopped')
        self.danceIndicatorLabel = Label(self.topFrame, textvar = self.danceIndicatorVar, width = 9, height = 2, font=('Tahoma', 14), fg = 'darkred', relief = 'sunken')
        self.danceIndicatorLabel.grid(row = 1, column = 7, rowspan = 2, sticky = E+W)
     
        #### Tempo frame #####################################################
        self.tempoFrame = LabelFrame(self.topFrame)
        self.tempoFrame.grid(row = 1, column = 9, rowspan = 3, sticky = E+N+S)

        Label(self.tempoFrame, text = '  ').grid(row = 1, column = 0)
        Button(self.tempoFrame, text = 'Reset tempo', width = 10, command = self.resetTempo).grid(row = 0, column = 1)
        self.maxEnergyVar = StringVar()
        Label(self.tempoFrame, textvar = self.maxEnergyVar, width = 10).grid(row = 1, column = 1)
        Label(self.tempoFrame, text = '  ').grid(row = 1, column = 2)
    
        ###### Indicatior frame #########
        self.indicatorFrame = Frame(self.tempoFrame)
        self.indicatorFrame.grid(row = 0, column = 3, sticky = E)

        Label(self.indicatorFrame, text = 'Tempo').grid(row = 0, column = 0)
        self.canvas0 = Canvas(self.indicatorFrame, width = 30, height = 30)
        self.circle0 = self.canvas0.create_oval(3,3,28,28, fill = '#550')
        self.canvas0.grid(row = 1, column = 0)

        Label(self.indicatorFrame, text = '\t').grid(row = 0, column = 1)
        
        Label(self.indicatorFrame, text = 'Sync').grid(row = 0, column = 2)
        self.canvas1 = Canvas(self.indicatorFrame, width = 30, height = 30)
        self.circle1 = self.canvas1.create_oval(3,3,28,28, fill = '#050')
        self.canvas1.grid(row = 1, column = 2)
        
        Label(self.indicatorFrame, text = '\t').grid(row = 0, column = 3)

        Label(self.indicatorFrame, text = 'Beat').grid(row = 0, column = 4)
        self.canvas2 = Canvas(self.indicatorFrame, width = 30, height = 30)
        self.circle2 = self.canvas2.create_oval(3,3,28,28, fill = '#500')
        self.canvas2.grid(row = 1, column = 4)

        Label(self.indicatorFrame, text = '\t').grid(row = 0, column = 5)

        Label(self.indicatorFrame, text = 'Sound level').grid(row = 0, column = 6)
        self.canvas3 = Canvas(self.indicatorFrame, width = 30, height = 30)
        self.rectangle0 = self.canvas3.create_rectangle(3,3,28,28, outline = 'black')
        self.rectangle3 = self.canvas3.create_rectangle(4,15,28,28, fill = 'red', width = 0)
        self.canvas3.grid(row = 1, column = 6)

        ###### BPM frame #########
        self.bpmFrame = Frame(self.tempoFrame)
        self.bpmFrame.grid(row = 2, column = 1, columnspan = 3, sticky = W)

        Label(self.bpmFrame, text = 'BPM:').grid(row = 0, column = 0, sticky = E)
        self.tempoVar = IntVar()
        Label(self.bpmFrame, textvar = self.tempoVar, width = 5, relief = 'sunken').grid(row = 0, column = 1, sticky = W)

        Label(self.bpmFrame, text = '  ').grid(row = 0, column = 2)
        self.incBPMButton = Button(self.bpmFrame, text="+", width = 2, repeatinterval = 50, repeatdelay = 500, command = self.incBPM)
        self.incBPMButton.grid(row = 0, column = 3)
        self.incBPMButton.config(state = 'disabled')
        self.decBPMButton = Button(self.bpmFrame, text="-", width = 2, repeatinterval = 50, repeatdelay = 500, command = self.decBPM)
        self.decBPMButton.grid(row = 0, column = 4)
        self.decBPMButton.config(state = 'disabled')
        Label(self.bpmFrame, text = '  ').grid(row = 0, column = 5)
        self.generateBeat = IntVar()
        Checkbutton(self.bpmFrame, text = 'Generate beat', var = self.generateBeat, command = self.setBPM).grid(row = 0, column = 6)

        ###### executing Frame #########
        self.execMoveFrame = LabelFrame(self.topFrame)
        self.execMoveFrame.grid(row = 3, column = 1, columnspan = 7, sticky = W+S)
        
        Label(self.execMoveFrame, text =      ' Nr/ID     Name                           Type   Step  Rep.', font = ("Courier", 9)).grid(row = 0, column = 0)
        self.execMoveLabelVar = StringVar(value = ' ---- | ------------------------------ | ------ | -- | -- ')
        Label(self.execMoveFrame, textvar = self.execMoveLabelVar, width = 58, relief = 'sunken', font = ("Courier", 9)).grid(row = 1, column = 0)

        Label(self.topFrame, text = '  ').grid(row = 5, column = 8)
        
        ## Middle Frame #####################################################################################
        self.middleFrame = Frame(self.frame)
        self.middleFrame.grid(row = 1, column = 0)
        
        Label(self.middleFrame, text="   ").grid(row = 1, column = 0)
        ######################### Sequence frame ####################################
        self.sequenceFrame = LabelFrame(self.middleFrame, text = 'Sequence:')
        self.sequenceFrame.grid(row = 1, column = 1, sticky = W+N+S)

        self.sequence = []
                                    
        Label(self.sequenceFrame, text=" Nr:  ID:   Name:           Repeat:", font = ("Courier", 9)).grid(row = 0, column = 0, columnspan = 6, sticky = W)
        self.sequenceListFrame = Frame(self.sequenceFrame)
        self.sequenceListFrame.grid(row = 1, column = 0, columnspan = 6, sticky = W)
        scrollBar = Scrollbar(self.sequenceListFrame)
        scrollBar.grid(row = 0, column = 1, sticky = N+S)
        self.sequenceListBox = Listbox(self.sequenceListFrame, width = 35, height = 13, selectmode = SINGLE, activestyle = NONE, exportselection = 0, font = ("Courier", 9))
        self.sequenceListBox.grid(row = 0, column = 0)
        scrollBar.config(command = self.sequenceListBox.yview)
        self.sequenceListBox.config(yscrollcommand = scrollBar.set)

        Label(self.sequenceFrame, text=" ").grid(row = 3, column = 0)
        Button(self.sequenceFrame, text = 'Load', command = self.loadSequence, width = 8).grid(row = 3, column = 1)
        Button(self.sequenceFrame, text = 'Save', command = self.saveSequence, width = 8).grid(row = 3, column = 2)
        Button(self.sequenceFrame, text = 'Clear', command = self.clearSequence, width = 8).grid(row = 3, column = 3)
        Button(self.sequenceFrame, text = 'Remove', command = self.removeFromSequence, width = 8).grid(row = 3, column = 4)
        Label(self.sequenceFrame, text=" ").grid(row = 3, column = 5)

        ######################### add to Sequence ####################################
        self.addFrame = LabelFrame(self.middleFrame)
        self.addFrame.grid(row = 1, column = 2, sticky = S)
        
        Label(self.addFrame, text = 'Repeat:').grid(row = 0, column = 0, columnspan = 2)
        Label(self.addFrame, text = 'Min').grid(row = 1, column = 0, sticky = E)
        self.repeatMoveVar = IntVar(value = 3)
        self.repeatMoveOList = range(1,11)
        self.repeatMoveOm = OptionMenu(self.addFrame, self.repeatMoveVar, *self.repeatMoveOList)
        self.repeatMoveOm.grid(row = 1, column = 1, sticky = W)
        self.repeatMoveOm.config(width = 2)
        self.repeatExactly = IntVar()
        Checkbutton(self.addFrame, text = 'Exactly', var = self.repeatExactly).grid(row = 2, column = 0, columnspan = 2, sticky = W)

        Button(self.addFrame, text = '<- Insert', command = self.insertToSequence, width = 10, height = 1).grid(row = 3, column = 0, columnspan = 2)
        Button(self.addFrame, text = '<- Append', command = self.appendToSequence, width = 10, height = 1).grid(row = 4, column = 0, columnspan = 2)

        ######################### Moves frame ####################################
        self.movesFrame = LabelFrame(self.middleFrame, text = 'Dance moves database:')
        self.movesFrame.grid(row = 1, column = 3, sticky = W+N+S)

        self.moveList = []
        self.lastMoveID = 0
                                    
        Label(self.movesFrame, text=" ID:    Name:             Type: Music:", font = ("Courier", 9)).grid(row = 0, column = 0, columnspan = 3, sticky = W)
        self.movesListFrame = Frame(self.movesFrame)
        self.movesListFrame.grid(row = 1, column = 0, rowspan = 10, columnspan = 3, sticky = W)
        scrollBar = Scrollbar(self.movesListFrame)
        scrollBar.grid(row = 0, column = 3, sticky = N+S)
        self.moveListBox = Listbox(self.movesListFrame, width = 37, height = 12, selectmode = SINGLE, activestyle = NONE, font = ("Courier", 9))
        self.moveListBox.grid(row = 0, column = 0)
        scrollBar.config(command = self.moveListBox.yview)
        self.moveListBox.config(yscrollcommand = scrollBar.set)
        self.moveListBox.bind('<ButtonRelease-1>', self.selectMove)

        ### selected move frame ####
        self.selectedMoveFrame = LabelFrame(self.movesFrame)
        self.selectedMoveFrame.grid(row = 11, column = 0, columnspan = 6, sticky = W+E+N+S)

        Label(self.selectedMoveFrame, text = ' Name:').grid(row = 0, column = 0, sticky = E)
        self.selectedMoveLabel = StringVar()
        Label(self.selectedMoveFrame, textvar = self.selectedMoveLabel, anchor = W, width = 45, relief = 'sunken').grid(row = 0, column = 1, columnspan = 3, sticky = W)

        Label(self.selectedMoveFrame, text = ' Steps:').grid(row = 0, column = 3, columnspan = 2, sticky = E)
        self.selectedMoveStepsLabel = StringVar()
        Label(self.selectedMoveFrame, textvar = self.selectedMoveStepsLabel, width = 4, relief = 'sunken').grid(row = 0, column = 5, sticky = E)
        
        Label(self.selectedMoveFrame, text = ' Types:').grid(row = 1, column = 0, sticky = E)
        self.selectedMoveTypesLabel = StringVar(value = 'Single, Double, Pulse')
        Label(self.selectedMoveFrame, textvar = self.selectedMoveTypesLabel, anchor = W, width = 20, relief = 'sunken').grid(row = 1, column = 1, sticky = W)
        
        Label(self.selectedMoveFrame, text = ' Music:').grid(row = 1, column = 2, sticky = E)
        self.selectedMoveMusicLabel = StringVar(value = 'Slow, Fast, No beat')
        Label(self.selectedMoveFrame, textvar = self.selectedMoveMusicLabel, anchor = W, width = 20, relief = 'sunken').grid(row = 1, column = 3,  columnspan = 3, sticky = W)

        ### buttons ####
        Label(self.movesFrame, text="\t").grid(row = 5, column = 4)
        self.createMoveButton = Button(self.movesFrame, text = 'Create', command = self.createMove, width = 8)
        self.createMoveButton.grid(row = 5, column = 5)
        self.editMoveButton = Button(self.movesFrame, text = 'Edit', command = self.editMove, width = 8)
        self.editMoveButton.grid(row = 6, column = 5)
        self.deleteMoveButton = Button(self.movesFrame, text = 'Delete', command = self.deleteMove, width = 8)
        self.deleteMoveButton.grid(row = 7, column = 5)
        Label(self.movesFrame, text=" ").grid(row = 8, column = 3)
        self.importMoveButton = Button(self.movesFrame, text = 'Import', command = self.importMove, width = 8)
        self.importMoveButton.grid(row = 9, column = 5)
        self.exportMoveButton = Button(self.movesFrame, text = 'Export', command = self.exportMove, width = 8)
        self.exportMoveButton.grid(row = 10, column = 5)
        Label(self.movesFrame, text=" ").grid(row = 8, column = 6)

        ############################################################################
        Label(self.middleFrame, text="   ").grid(row = 1, column = 4)
        
        ## Bottom Frame #####################################################################################
        Label(self.frame, text="\t").grid(row = 2, column = 0)
        self.oneMove = frameOneMove(self.frame, self, self.servoDict, row = 3, column = 0)  #one move frame (bottom)


        ##### Initialization 
        self.autoLoadMoves()   # load move list
        self.stepCounter = 0
        self.repeatCounter = 0
        self.sequenceCounter = 0
        self.currentType = 'Single'
        self.currentRepeat = 1
        self.curentDanceMove = []
        self.currentMusic = 'Slow'
        self.dancing = False
        self.noBeat = False
        self.generatedBPM = 120
        self.lastTime = 0

    ### The main loop
    def Loop(self):
        if self.on:
            delay = 4
            instant_energy = 0
            sync = False
            beat = False
            tempo = False
            
            if not self.generateBeat.get():
                #### get audio sample and calculate instant signal energy
                data = self.stream.read(self.chuck)
                indata = np.array(wave.struct.unpack("%dh"%(self.chuck), data), dtype = float)
                instant_energy1 = np.dot(indata[0:1024],indata[0:1024])/float(0xffffffff)/self.chuck
                instant_energy2 = np.dot(indata[1024:],indata[1024:])/float(0xffffffff)/self.chuck
                instant_energy = max(instant_energy1, instant_energy2)
                
                if self.max_energy < instant_energy:
                    self.max_energy = instant_energy
                else:
                    self.max_energy *= 0.9995 #0.9999

                if instant_energy < 1e-5:
                    self.countS += 1
                    self.max_energy *= 0.995   # faster decay of max_energy
                else:
                    self.countS = 0

                if  self.countS  > 2*44100/self.chuck:  # if silence for more that 2 seconds, reset tempo
                    self.tempo = 0

##                self.maxEnergyVar.set("%1.7f" % self.max_energy)

                #### detect beat and synchronize tempo
                beat = instant_energy > 0.5*self.max_energy
                if beat and self.countB > 2:  
                    self.countB_hist.append(self.countB)
                    if len(self.countB_hist) > 3:
                        self.countB_hist.pop(0)

                    self.countB = 1

                    if len(self.countB_hist) == 3:
                        if self.tempo == 0:   # no tempo detected yet
                            # detected at least 3 beats equaly spaced in time                      
                            if abs(self.countB_hist[2] - self.countB_hist[1]) < 2 and self.countB_hist[2] > 6 and self.countB_hist[2] < 25:
                                self.tempo = (self.countB_hist[1]+self.countB_hist[2])/2.0 # create tempo
                                self.tempoNr = 1
                                self.countT = 1   # sync
                                sync = True
                        else:                                   
                            if abs(sum(self.countB_hist) - 3*self.tempo) < 5 and max(self.countB_hist) - min(self.countB_hist) < 3:  # 3 consecutive beats
                                if self.tempoNr < 50:  # floating filter limit
                                    self.tempoNr += 1 
                                self.tempo = self.tempo*(self.tempoNr-1)/self.tempoNr + (sum(self.countB_hist)/3.0)/self.tempoNr # update tempo
                                self.countT = 1   # sync
                                sync = True                                       
                            elif abs(sum(self.countB_hist[1:3]) - 2*self.tempo) < 4 and abs(self.countB_hist[2] - self.countB_hist[1]) < 3:  # 2 consecutive beats
                                if self.tempoNr < 50:  # floating filter limit
                                    self.tempoNr += 1  
                                self.tempo = self.tempo*(self.tempoNr-1)/self.tempoNr + ((self.countB_hist[1]+self.countB_hist[2])/2.0)/self.tempoNr # update tempo
                                self.countT = 1   # sync
                                sync = True
                else:
                    self.countB += 1
            else:
                self.tempo = 44100/float(self.chuck)*60/self.generatedBPM
                self.countB = 0
                now = time.time()
                while now - self.lastTime < float(self.chuck)/44100:
                    time.sleep(0.005)
                    now = time.time()
                self.lastTime = now
    
            
            if self.tempo == 0 and not self.noBeat:  # no beat move at the beginning of the song
                self.getNoBeatMove()
                self.noBeat = True

            #### tempo loop
            if round(self.countT + delay - self.tempo) >= 0 and self.tempo != 0:
                if self.dancing:
                    if self.countB > 3*self.tempo and self.countB > 30:  # no beat detected for at least 3 tempos, activate noBeat  (during, end of the song)
                        if not self.noBeat:
                            self.getNoBeatMove()
                        self.noBeat = True
                        if instant_energy > 0.0001*self.max_energy: # do no-beat move only if music is playing (otherwise it would look silly)
                            self.doNextMove()
                    else:
                        self.noBeat = False
                        self.doNextMove()
                self.countM = 0
                self.countT -= self.tempo - 1
                if self.generateBeat.get():
                    beat = True
                    sync = True  
            else:
                if self.dancing:
                    if self.noBeat and instant_energy > 0.0001*self.max_energy:
                        self.doNextMove()
                    else:
                        if self.currentType == 'Pulse' and  self.countM == 1 and self.stepCounter != 0: 
                            self.doNextMove()
                            
                        if self.currentType == 'Double' and  self.countM == int(self.tempo/2) and self.stepCounter != 0:
                            self.doNextMove()
                if self.countM  == delay:
                    tempo = True
                self.countT += 1
                self.countM += 1
                

            if beat:
                self.canvas2.itemconfigure(self.circle2, fill = '#F00')
            else:
                self.canvas2.itemconfigure(self.circle2, fill = '#500')

            if sync:
                self.canvas1.itemconfigure(self.circle1, fill = '#0F0')
            else:
                self.canvas1.itemconfigure(self.circle1, fill = '#050')

            if tempo:
                self.canvas0.itemconfigure(self.circle0, fill = '#DD0')
            else:
                self.canvas0.itemconfigure(self.circle0, fill = '#550')


            self.canvas3.coords(self.rectangle3, 4, int(4 - 4*np.log10(instant_energy + 1e-6)), 28, 28)

            if self.tempo != 0:
                BPM = int(44100/float(self.chuck)*60/self.tempo)
                self.tempoVar.set(BPM)
                if BPM > 120:
                    self.currentMusic = 'Fast'
                else:
                    self.currentMusic = 'Slow'
            else:
                self.tempoVar.set(0)

    def doNextMove(self):
        # no-beat music period
        if self.noBeat:  
            if self.curentDanceMove.canMusic('No beat') and self.curentDanceMove.length > 1:
                #### go slowly from step 1 to step 2 and back, in 4*k steps
                k = 20
                if self.countNB % 2 == 0:  # send only once per 2 cycles
                    if self.countNB < k:  
                        for i in range(len(self.servoDict)):
                            angle = (self.step1ServosPos[i]*(k - self.countNB) + self.step2ServosPos[i]*self.countNB)/float(k)
                            self.con.servos[self.servoDict[i]].setPos(deg = angle, move = False)
                        self.con.sendBinary()
                    elif 2*k <= self.countNB < 3*k:
                        for i in range(len(self.servoDict)):
                            angle = (self.step1ServosPos[i]*(self.countNB - 2*k) + self.step2ServosPos[i]*(3*k - self.countNB))/float(k)
                            self.con.servos[self.servoDict[i]].setPos(deg = angle, move = False)
                        self.con.sendBinary()
                self.countNB += 1
                self.countNB %= 4*k
                
        # beat detected repeatedly - perform normal dance move     
        else:
            s = self.execMoveLabelVar.get()
            
            if self.stepCounter == 0:   # new step counting
                if self.repeatCounter == 0:     # new repeat counting, pick new dance move
                    canMusic = False
                    zeroSteps = True
                    # go through list of moves and find the one which can this music speed and has at least one dance step
                    while not canMusic or zeroSteps:   
                        # if sequence list is empty or want to pick from all moves
                        if len(self.sequence) == 0 or self.whichList.get():
                            if self.randomVar.get():              # random order
                                index = int(random()*len(self.moveList))
                                self.curentDanceMove = self.moveList[index]
                            else:                                  # sequentially
                                self.sequenceCounter %= len(self.moveList)
                                self.curentDanceMove = self.moveList[self.sequenceCounter]
                                self.sequenceCounter += 1
                                self.sequenceCounter %= len(self.moveList)
                    
                            self.currentRepeat = 3 + int(random()*8)   # repeat the move between 3 and 20 times
                            
                        # otherwise pick from the sequence list
                        else:
                            x = []
                            while x == []:
                                if self.randomVar.get():            # random order
                                    index = int(random()*len(self.sequence))
                                else:                              # sequentially 
                                    self.sequenceCounter %= len(self.sequence)
                                    index = self.sequenceCounter
                                    self.sequenceCounter += 1   
                                    self.sequenceCounter %= len(self.sequence)
                                                
                                ID = self.sequence[index][0]        # sequence list stores only move ID, not the whole move
                                x = [x for x in self.moveList if x.ID == ID]   # search in moveList based on the move ID number
                                if x != []:    # found the move
                                    self.curentDanceMove = x[0]
                                                
                            if self.sequence[index][2]:                  # if repeat exactly flag
                                self.currentRepeat = self.sequence[index][1]
                            else:
                                self.currentRepeat = self.sequence[index][1] + int(random()*(11-self.sequence[index][1]))
                                   
                        canMusic = self.curentDanceMove.canMusic(self.currentMusic)  # can the current music speed
                        zeroSteps = (self.curentDanceMove.length == 0)

                    # get dance type (single, double, pulse), random choice if more than one possible, 'Single' if no choice
                    if len(self.curentDanceMove.type) > 0:  
                        self.currentType = self.curentDanceMove.type[int(len(self.curentDanceMove.type)*random())]
                    else:
                        self.currentType = 'Single'

                    # update execMoveLabel based on the picked move 
                    if self.whichList.get() == 0 and len(self.sequence) and not self.randomVar.get():
                        if self.sequenceCounter == 0:
                            sc = len(self.sequence)
                        else:
                            sc = self.sequenceCounter 
                        s =  '  %2d  ' % (sc)
                    else:
                        s =  ' %04d ' % (self.curentDanceMove.ID)
                    s += '|                                |        |    |    '
                    n = min(len(self.curentDanceMove.name),30)
                    s = s[0:8] + self.curentDanceMove.name[0:30] + s[8+n:]
                    n = min(len(self.currentType),6)
                    s = s[0:41] + self.currentType[0:6] + s[41+n:]

                s = s[0:55] + '%2d' % (self.currentRepeat - self.repeatCounter) + ' '
                self.repeatCounter += 1
                self.repeatCounter %= self.currentRepeat

            # get next step of the current dance move
            step = self.curentDanceMove.getStep(self.stepCounter)

            self.stepCounter += 1
            s = s[0:50] + '%2d' % self.stepCounter + s[52:]
            self.stepCounter %= self.curentDanceMove.length

            # get new servo values from Inverse-kinematic robot model 
            if (step[0] == 'walk'):
                self.Robot.updateRobot(pos = step[1][0][0:3], angle = step[1][0][3:6], move = True, dPos = step[1][1], send = False)
            else:
                self.Robot.updateRobot(pos = step[1][0][0:3], angle = step[1][0][3:6], move = False, send = False)
                
                # if there are manual servo values, update them as well
                servoNr = step[1][1]
                for i in range(servoNr):
                    [servo, angle, move] = step[1][2+i]
                    if move == 'R':
                        angle += self.con.servos[servo].getPosDeg()
                    angle = min(max(angle, -80), 80)
                    self.con.servos[servo].setPos(deg = angle, move = False)
                    
            # send to robot
            self.con.sendBinary()
            # update Label
            self.execMoveLabelVar.set(s)

    def getNoBeatMove(self):
        self.countNB = 0        # reset no-beat counter

        if not self.curentDanceMove:
            self.curentDanceMove = self.moveList[0]
        
        if self.curentDanceMove.canMusic('No beat') and self.curentDanceMove.length > 1:
            step1 = self.curentDanceMove.getStep(0)
            step2 = self.curentDanceMove.getStep(1)
            if step1[0] == 'no walk' and  step2[0] == 'walk':   # is the second step is walk, than the 3rd must be walk as well
                step1 = self.curentDanceMove.getStep(2)
            ############## Get all servo positions for step 1
            if (step1[0] == 'walk'):
                self.Robot.updateRobot(step1[1][0][0:3], step1[1][0][3:6], move = True, dPos = step1[1][1], send = False)
            else:
                self.Robot.updateRobot(step1[1][0][0:3], step1[1][0][3:6], move = False, send = False)
                servoNr = step1[1][1]
                for i in range(servoNr):
                    [servo, angle, move] = step1[1][2+i]
                    if move == 'R':
                        angle += self.con.servos[servo].getPosDeg()
                    angle = min(max(angle, -80), 80)
                    self.con.servos[servo].setPos(deg = angle, move = False)

            self.step1ServosPos = []
            for i in range(len(self.servoDict)):
                self.step1ServosPos.append(self.con.servos[self.servoDict[i]].getPosDeg())
                
            ############## Get all servo positions for step 2
            if (step2[0] == 'walk'):
                self.Robot.updateRobot(step2[1][0][0:3], step2[1][0][3:6], move = True, dPos = step2[1][1], send = False)
            else:
                self.Robot.updateRobot(step2[1][0][0:3], step2[1][0][3:6], move = False, send = False)
                servoNr = step2[1][1]
                for i in range(servoNr):
                    [servo, angle, move] = step2[1][2+i]
                    if move == 'R':
                        angle += self.con.servos[servo].getPosDeg()
                    angle = min(max(angle, -80), 80)
                    self.con.servos[servo].setPos(deg = angle, move = False)

            self.step2ServosPos = []
            for i in range(len(self.servoDict)):
                self.step2ServosPos.append(self.con.servos[self.servoDict[i]].getPosDeg())

            s = self.execMoveLabelVar.get()
            s = s[0:50] + 'NB' + s[52:]
            self.execMoveLabelVar.set(s)
        

    def startDance(self):
        self.danceIndicatorVar.set('Dancing')
        self.danceIndicatorLabel.config(fg = '#080')
        self.dancing = True

    def pauseDance(self):
        self.danceIndicatorVar.set('Paused')
        self.danceIndicatorLabel.config(fg = '#a80')
        self.dancing = False

    def stopDance(self):
        self.danceIndicatorVar.set('Stopped')
        self.danceIndicatorLabel.config(fg = '#800')
        self.stepCounter = 0
        self.repeatCounter = 0
        self.sequenceCounter = 0
        self.dancing = False

    def resetTempo(self):
        self.max_energy /= 2
        self.tempo = 0
    
    def incBPM(self):
        self.generatedBPM += 1
        if self.generatedBPM > 180:
            self.generatedBPM = 180

    def decBPM(self):
        self.generatedBPM -= 1
        if self.generatedBPM < 40:
            self.generatedBPM = 40

    def setBPM(self):
        self.tempo = 0
        if self.generateBeat.get():
            self.incBPMButton.config(state = 'active')
            self.decBPMButton.config(state = 'active')
        else:
            self.incBPMButton.config(state = 'disabled')
            self.decBPMButton.config(state = 'disabled')

    def createMove(self):
        index = len(self.moveList)
        self.oneMove.show(self.moveList, index, self.lastMoveID, 'Create move:')
        
        self.createMoveButton.config(state = 'disabled')
        self.editMoveButton.config(state = 'disabled')
        self.deleteMoveButton.config(state = 'disabled')
        self.importMoveButton.config(state = 'disabled')
        self.exportMoveButton.config(state = 'disabled')
        self.startDanceButton.config(state = 'disabled')
        if self.dancing:
            self.pauseDance()

    def editMove(self):      
        try:
            index = int(self.moveListBox.curselection()[0])
            temp = self.moveList[index]
            self.oneMove.show(self.moveList, index, self.lastMoveID, 'Edit move:')
            
            self.createMoveButton.config(state = 'disabled')
            self.editMoveButton.config(state = 'disabled')
            self.deleteMoveButton.config(state = 'disabled')
            self.importMoveButton.config(state = 'disabled')
            self.exportMoveButton.config(state = 'disabled')
            self.startDanceButton.config(state = 'disabled')
            if self.dancing:
                self.pauseDance()
        except IndexError:
            pass
            
    def deleteMove(self):
        try:
            index = int(self.moveListBox.curselection()[0])
            if askretrycancel('Delete move','Deleting move will disable it in all saved sequence lists and cannot be reversed.\n\t\t\tAre you sure?'):
                del self.moveList[index]
                self.refreshMoveListBox()
                self.refreshSequenceListBox()
                self.autoSaveMoves()
        except IndexError:
            pass

    def autoLoadMoves(self):
        try:
            f = open('Dance\\dance moves.sav','r')
            if cPickle.load(f) == 'dance moves':
                self.moveList = cPickle.load(f)
                self.lastMoveID = cPickle.load(f)
                self.refreshMoveListBox()
            f.close()
        except:
            pass

    def autoSaveMoves(self):
        f = open('Dance\\dance moves.sav','w')
        cPickle.dump('dance moves', f)
        cPickle.dump(self.moveList, f)
        cPickle.dump(self.lastMoveID, f)
        f.close()
                     
    def importMove(self):
        try:
            f = askopenfile(filetypes = [('Dance move', '*.txt'),("All Files",".*")], defaultextension="*.txt", initialdir = 'Dance\\')
            if cPickle.load(f) == 'dance move':
                dM = cPickle.load(f)
                self.lastMoveID += 1
                dM.ID = self.lastMoveID
                self.moveList.append(dM)
                self.refreshMoveListBox()
                self.autoSaveMoves()
            f.close()
        except:
            pass

    def exportMove(self):
        try:
            index = int(self.moveListBox.curselection()[0])
            f = asksaveasfile(filetypes = [('Dance move', '*.txt'),("All Files",".*")], defaultextension="*.txt", initialdir = 'Dance\\')
            cPickle.dump('dance move', f)
            cPickle.dump(self.moveList[index], f)
            f.close()
        except:
            pass

    def selectMove(self, event = []):
        try:
            index = int(self.moveListBox.curselection()[0])
            dM = self.moveList[index]
            self.selectedMoveLabel.set(dM.name)
            self.selectedMoveStepsLabel.set("%02d" % dM.length)
            s = ''
            if dM.canType('Single'):
                s += 'Single, '
            if dM.canType('Double'):
                s += 'Double, '
            if dM.canType('Pulse'):
                s += 'Pulse'
            self.selectedMoveTypesLabel.set(s)
            s = ''
            if dM.canMusic('Slow'):
                s += 'Slow, '
            if dM.canMusic('Fast'):
                s += 'Fast, '
            if dM.canMusic('No beat'):
                s += 'No beat'
            self.selectedMoveMusicLabel.set(s)
        except IndexError:
            if len(self.moveList) > 0:
                index = len(self.moveList)-1
                self.moveListBox.selection_set(index)
                self.moveListBox.see(index)
                dM = self.moveList[index]
                self.selectedMoveLabel.set(dM.name)
                self.selectedMoveStepsLabel.set("%02d" % dM.length)
                s = ''
                if dM.canType('Single'):
                    s += 'Single, '
                if dM.canType('Double'):
                    s += 'Double, '
                if dM.canType('Pulse'):
                    s += 'Pulse'
                self.selectedMoveTypesLabel.set(s)
                s = ''
                if dM.canMusic('Slow'):
                    s += 'Slow, '
                if dM.canMusic('Fast'):
                    s += 'Fast, '
                if dM.canMusic('No beat'):
                    s += 'No beat'
                self.selectedMoveMusicLabel.set(s)

    def refreshMoveListBox(self, index = -1):
        self.moveListBox.delete(0,END)
        for i in range(len(self.moveList)):
            dM = self.moveList[i]
            s = "%04d" % dM.ID + '|                    |     |     '
            nLenght = min(len(dM.name),20)
            s = s[0:5] + dM.name[0:20] + s[5+nLenght:]
            s = list(s)
            if dM.canType('Single'):
                s[26] = 'S'
            if dM.canType('Double'):
                s[28] = 'D'
            if dM.canType('Pulse'):
                s[30] = 'P'
            if dM.canMusic('Slow'):
                s[32] = 'S'
            if dM.canMusic('Fast'):
                s[34] = 'F'
            if dM.canMusic('No beat'):
                s[36] = 'N'
            s = ''.join(s)
            self.moveListBox.insert(END,s)
        self.moveListBox.selection_set(index)
        self.moveListBox.see(index)
        self.selectMove()

    def refreshSequenceListBox(self, index = -1):
        self.sequenceListBox.delete(0,END)
        for i in range(len(self.sequence)):
            s = "%3d |" % (i+1)
            s += "%04d|" % self.sequence[i][0] + '|                   |'     
            ID = self.sequence[i][0]
            x = [x for x in self.moveList if x.ID == ID]   # search in moveList based on Move ID number
            if x != []:
                dM = x[0]
                nLenght = min(len(dM.name),20)
                s = s[0:10] + dM.name[0:20] + s[10+nLenght:]
                s += "% 2d" % self.sequence[i][1]
                if not self.sequence[i][2]:
                    s += '+'
            else:
                s = s[0:10] + '--------------------|---'    # if move was not find, it was deleted
            self.sequenceListBox.insert(END,s)
        self.sequenceListBox.selection_set(index)
        self.sequenceListBox.see(index)

    def loadSequence(self):
        try:
            f = askopenfile(filetypes = [('Sequence', '*.seq'),("All Files",".*")], defaultextension="*.seq", initialdir = 'Dance\\')
            if cPickle.load(f) == 'dance move sequence':
                self.sequence = cPickle.load(f)
                self.refreshSequenceListBox()
            f.close()
        except:
            pass

    def saveSequence(self):
        f = asksaveasfile(filetypes = [('Sequence', '*.seq'),("All Files",".*")], defaultextension="*.seq", initialdir = 'Dance\\')
        cPickle.dump('dance move sequence', f)
        cPickle.dump(self.sequence, f)
        f.close()

    def clearSequence(self):
        self.sequence = []
        self.refreshSequenceListBox()

    def removeFromSequence(self):
        try:
            index = int(self.sequenceListBox.curselection()[0])
            del self.sequence[index]
            self.refreshSequenceListBox()
        except IndexError:
            pass

    def insertToSequence(self):
        try:
            index = int(self.moveListBox.curselection()[0])
            index2 = int(self.sequenceListBox.curselection()[0])
            dM = self.moveList[index]
            self.sequence.insert(index2, (dM.ID, self.repeatMoveVar.get(), self.repeatExactly.get() == 1))
            self.refreshSequenceListBox(index = index2)
            self.refreshMoveListBox(index = index)
        except IndexError:
            self.appendToSequence()
        
    def appendToSequence(self):
        try:
            index = int(self.moveListBox.curselection()[0])
            dM = self.moveList[index]
            self.sequence.append((dM.ID, self.repeatMoveVar.get(), self.repeatExactly.get() == 1))
            self.refreshSequenceListBox(index = len(self.sequence)-1)
            self.refreshMoveListBox(index = index)
        except IndexError:
            pass    

    def show(self):
        self.frame.grid(row = self.rowY, column = self.colX, rowspan = 100, columnspan = 100, sticky = N+W)
        self.Robot.initRobot(70)
        self.on = True
        
    def hide(self):
        self.frame.grid_forget()
        self.on = False
#########################################################################################################################
#########################################################################################################################
        
def startGUI(controller):
    global root 
    root = Tk()

    global app
    app = App(root,controller)
    root.mainloop()

    
    
