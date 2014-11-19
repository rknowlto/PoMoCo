import time
import math
import numpy as np

from servotorComm import runMovement

# Modifies how smoothly the servos move.
# Smoother means more processing power, and fills the serial line.
# Lower if movements start to slow down, or get weird.
# Anything higher than 50 is pointless ( faster than the maximum refresh of standard servos ).
stepPerS = 5

class hexapod():

    def __init__(self,con):
        self.con = con
        
        self.RF  = leg(con,'rightFront',24,25,26,'right')
        self.RM  = leg(con,'rightMid',20,21,22,'right')
        self.RB  = leg(con,'rightBack',16,17,18,'right')

        self.LF  = leg(con,'leftFront',7,6,5,'left')
        self.LM  = leg(con,'leftMid',11,10,9,'left')
        self.LB  = leg(con,'leftBack',15,14,13,'left')

        self.legs = [self.RF,
                     self.RM,
                     self.RB,
                     self.LF,
                     self.LM,
                     self.LB]

        self.neck = neck(con,31)

        self.tripod1 = [self.RF,self.RB,self.LM]
        self.tripod2 = [self.LF,self.LB,self.RM]
#################################################################################################
#################################################################################################
class neck():
    def __init__(self,con,servoNum):
        self.con = con
        self.servoNum = servoNum

    def set(self,deg):
        self.con.servos[self.servoNum].setPos(deg=deg)
#################################################################################################
#################################################################################################
class leg():

    def __init__(self,con,name,hipServoNum,kneeServoNum,ankleServoNum,side = 'left',simOrigin=(0,3,0)):
        self.con = con
        self.name = name
        self.hipServoNum = hipServoNum
        self.kneeServoNum = kneeServoNum
        self.ankleServoNum = ankleServoNum

        if side == 'right' and legsMirrored:
            self.side = -1.0
        else:
            self.side = 1.0

    def hip(self, deg):
        if deg == "sleep":
            self.con.servos[self.hipServoNum].kill()
        else:
            self.con.servos[self.hipServoNum].setPos(deg = deg)

    def knee(self, deg):
        if deg == "sleep":
            self.con.servos[self.hipServoNum].kill()
        else:
            self.con.servos[self.kneeServoNum].setPos(deg = deg*self.side)

    def ankle(self, deg):
        if deg == "sleep":
            self.con.servos[self.hipServoNum].kill()
        else:
            self.con.servos[self.ankleServoNum].setPos(deg = (deg + ankleOffset)*self.side)

    def setHipDeg(self, endHipAngle, stepTime = 1):
        runMovement(self.setHipDeg_function, endHipAngle, stepTime)

##    def setFootY(self, footY, stepTime = 1):
    def setFootY(self, footY = 1000, footRx = 0, stepTime = 1):
        runMovement(self.setFootY_function, footY, footRx, stepTime)

    def replantFoot(self, endHipAngle, endAnkleAngle = 0,stepTime = 1):
        runMovement(self.replantFoot_function, endHipAngle, endAnkleAngle, stepTime)

    def pointCircle(self, centerHipAngle = 0, radius = 15, orientation = 1, stepTime = 0.5):
        runMovement(self.pointCircle_function, centerHipAngle, radius, orientation, stepTime)

#################################################################################################
    def setHipDeg_function(self,endHipAngle,stepTime):
        currentHipAngle = self.con.servos[self.hipServoNum].getPosDeg()
        hipMaxDiff = endHipAngle-currentHipAngle

        steps = range(int(stepPerS))
        for i,t in enumerate(steps):
            # TODO: Implement time-movements the servo commands sent for far fewer
            #       total servo commands
            hipAngle = (hipMaxDiff/len(steps))*(i+1)
            try:
                anglNorm=hipAngle*(180/(hipMaxDiff))
            except:
                anglNorm=hipAngle*(180/(1))
            hipAngle = currentHipAngle+hipAngle
            self.con.servos[self.hipServoNum].setPos(deg=hipAngle)

            #wait for next cycle
            time.sleep(stepTime/float(stepPerS))

    def setFootY_function(self,footY,footRx,stepTime):
        # TODO: Max step-time dependent
        # TODO: Implement time-movements the servo commands sent for far fewer
        #       total servo commands
        if (footY == 1000):
            footY = floor

        if (footY < 75) and (footY > -75):
            kneeAngle = math.degrees(math.asin(float(footY)/75.0))
            ankleAngle = ankleOffset - kneeAngle + footRx

            self.con.servos[self.kneeServoNum].setPos(deg=kneeAngle*self.side)
            self.con.servos[self.ankleServoNum].setPos(deg=-ankleAngle*self.side)        

    def replantFoot_function(self, endHipAngle, endAnkleAngle, stepTime):
    # Smoothly moves a foot from one position on the ground to another in time seconds
    # TODO: implement time-movements the servo commands sent for far fewer total servo
    #       commands

        currentHipAngle = self.con.servos[self.hipServoNum].getPosDeg()

        hipMaxDiff = endHipAngle-currentHipAngle

        steps = range(int(stepPerS))
        for i,t in enumerate(steps):

            hipAngle = (hipMaxDiff/len(steps))*(i+1)
            #print "hip angle calculated:",hipAngle

            # Calculate the absolute distance between the foot's highest and lowest point
            footMax = 0
            footMin = floor
            footRange = abs(footMax-footMin)

            # Normalize the range of the hip movement to 180 deg
            try:
                anglNorm=hipAngle*(180/(hipMaxDiff))
            except:
                anglNorm=hipAngle*(180/(1))
            #print "normalized angle:",anglNorm

            # Base footfall on a sin pattern from footfall to footfall with 0 as the midpoint
            footY = footMin-math.sin(math.radians(anglNorm))*footRange
            #print "calculated footY",footY

            # Set foot height
            self.setFootY(footY, endAnkleAngle, stepTime = 0)
            hipAngle = currentHipAngle + hipAngle
            self.con.servos[self.hipServoNum].setPos(deg=hipAngle)

            # Wait for next cycle
            time.sleep(stepTime/float(stepPerS))

    def pointCircle_function(self, centerHipAngle, radius, orientation, stepTime):
    # Waves in one circe
    
        if (orientation > 0):
            orientation = 1
        else:
            orientation = -1
    
        self.con.servos[self.hipServoNum].setPos(deg=centerHipAngle)
        self.con.servos[self.kneeServoNum].setPos(deg=radius*self.side)
        self.con.servos[self.ankleServoNum].setPos(deg=radius*self.side)
        time.sleep(stepTime/float(stepPerS))

        steps = range(int(stepPerS))
        for i,t in enumerate(steps):           

            hipAngle = centerHipAngle + math.sin(math.radians(orientation*(360/float(stepPerS-1)*i)))*radius
            kneeAngle = math.cos(math.radians(orientation*(360/float(stepPerS-1)*i)))*radius
            
            self.con.servos[self.hipServoNum].setPos(deg=hipAngle)
            self.con.servos[self.kneeServoNum].setPos(deg=kneeAngle*self.side)
            self.con.servos[self.ankleServoNum].setPos(deg=kneeAngle*self.side)
            
            # Wait for next cycle
            time.sleep(stepTime/float(stepPerS))
            
#################################################################################################
# Inverse-kinematic robot Hexy
# by Michal G., 01-07-2013
# - speed optimization (about 3x faster now)
# - new call parameter to postpone sending the data to Hexy
#################################################################################################
class kinematicRobot():
    def __init__(self, con, Dict):
        self.con = con
        self.Dict = self.reverseDict(Dict)
        self.bodyRadius = 100
        self.hip = 26
        self.thigh = 49
        self.foot = 55
        self.bodyAngle = 50.0/180*np.pi
        self.bodyAngles = [np.pi/2 - self.bodyAngle, np.pi/2, np.pi/2 + self.bodyAngle,
                          3*np.pi/2 - self.bodyAngle, 3*np.pi/2, 3*np.pi/2 + self.bodyAngle]

        self.CycleStep = 0  # counter for moving legs sychnronization 
        self.MovingLegs = 3 # how many legs are moving at once
        self.FootPos = np.zeros((6,3))  # X,Y,Z position of all feet
        self.footDist = 160 # nominal distance of foot from body center. Empirical value
        for i in range(6):  # reset feet position
            self.FootPos[i] = [self.footDist*np.cos(self.bodyAngles[i]),self.footDist*np.sin(self.bodyAngles[i]),0]

        d = self.bodyRadius
        self.body = np.array([[d*math.cos(self.bodyAngles[0]),d*math.sin(self.bodyAngles[0]),0],
                              [d*math.cos(self.bodyAngles[1]),d*math.sin(self.bodyAngles[1]),0],
                              [d*math.cos(self.bodyAngles[2]),d*math.sin(self.bodyAngles[2]),0],
                              [d*math.cos(self.bodyAngles[3]),d*math.sin(self.bodyAngles[3]),0],
                              [d*math.cos(self.bodyAngles[4]),d*math.sin(self.bodyAngles[4]),0],
                              [d*math.cos(self.bodyAngles[5]),d*math.sin(self.bodyAngles[5]),0]]).T
        self.body2 = self.RotZ(self.body,0.001)

        if legsMirrored:
            self.sign = [1,1,1,-1,-1,-1]
        else:
            self.sign = [1,1,1,1,1,1]

    # internal - reverse servo dictionary
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

    # internal - Rotation X,Y,Z
    def RotXYZ(self,pos,a):
        Rxyz = [[math.cos(a[2])*math.cos(a[1]), math.cos(a[2])*math.sin(a[1])*math.sin(a[0])-math.sin(a[2])*math.cos(a[0]), math.cos(a[2])*math.sin(a[1])*math.cos(a[0])+math.sin(a[2])*math.sin(a[0])],
                [math.sin(a[2])*math.cos(a[1]), math.sin(a[2])*math.sin(a[1])*math.sin(a[0])+math.cos(a[2])*math.cos(a[0]), math.sin(a[2])*math.sin(a[1])*math.cos(a[0])-math.cos(a[2])*math.sin(a[0])],
                [-math.sin(a[1])              , math.cos(a[1])*math.sin(a[0])                                             , math.cos(a[1])*math.cos(a[0])]]
        return np.dot(Rxyz,pos)

    # internal - Rotation Z
    def RotZ(self,pos,angle):
        Rz = [[math.cos(angle),-math.sin(angle),0],
              [math.sin(angle),math.cos(angle),0],
              [0,0,1]]
        return np.dot(Rz,pos) 

    # internal - build body and perform translation
    def buildBody(self, pos = [0,0,0], angle = [0,0,0]):
        b  = self.RotXYZ(self.body,angle).T + pos 
        b2 = self.RotXYZ(self.body2,angle).T + pos
        return b, b2

    # internal - shift all legs in X,Y,Rz
    def setFeetPosInc(self, (x, y, Rz) = (0,0,0)):   
        self.FootPos = self.RotZ(self.FootPos.T, Rz*np.pi/180).T + [x, y, 0]

    # set number of legs moving at once (1 to 3)
    def setMovingLegs(self, iMovingLegs = 2):
        if iMovingLegs > 0 and iMovingLegs < 4:
            self.CycleStep = 0
            self.MovingLegs = iMovingLegs

    # initialization
    def initRobot(self, z = 75):
        # get body on the ground (z = 35 mm)
        b = np.array([self.bodyRadius, 35])
        k = np.array([self.bodyRadius + self.hip, 35])
        f = np.array([self.footDist, 0])
        kf = np.linalg.norm(k - f)
        bf = np.linalg.norm(b - f)
        ankleAngle = np.arccos((self.thigh**2 + self.foot**2 - kf**2)/(2*self.thigh*self.foot))
        kneeAngle = np.arccos((self.hip**2 + kf**2 - bf**2)/(2*self.hip*kf)) + np.arccos((self.thigh**2 + kf**2 - self.foot**2)/(2*self.thigh*kf))
        for i in range(6):
            self.con.servos[self.Dict[i*3+1]].setPos(deg = int(-kneeAngle/np.pi*180 + 180)*self.sign[i], move = False)
            self.con.servos[self.Dict[i*3+2]].setPos(deg = int(ankleAngle/np.pi*180 - 180 + ankleOffset)*self.sign[i], move = False)
        self.con.sendBinary()

        time.sleep(0.5)
        # reset hip position
        for i in range(6):
            self.con.servos[self.Dict[i*3+0]].setPos(deg = 0)
        self.con.sendBinary()    

        time.sleep(0.3) 
        # get body to nominal height z
        b = np.array([self.bodyRadius, z])
        k = np.array([self.bodyRadius + self.hip, z])
        kf = np.linalg.norm(k - f)
        bf = np.linalg.norm(b - f)
        ankleAngle = np.arccos((self.thigh**2 + self.foot**2 - kf**2)/(2*self.thigh*self.foot))
        kneeAngle = np.arccos((self.hip**2 + kf**2 - bf**2)/(2*self.hip*kf)) + np.arccos((self.thigh**2 + kf**2 - self.foot**2)/(2*self.thigh*kf))
        for i in range(6):
            self.con.servos[self.Dict[i*3+1]].setPos(deg = int(-kneeAngle/np.pi*180 + 180)*self.sign[i], move = False)
            self.con.servos[self.Dict[i*3+2]].setPos(deg = int(ankleAngle/np.pi*180 - 180 + ankleOffset)*self.sign[i], move = False)
        self.con.sendBinary()    

    # update robot position - the main calculation loop
    def updateRobot(self, pos = (0,0,75), angle = (0,0,0), move = False, dPos = (0,0,0), send = True):
        """
        The idea is that during move the body stays still, but the legs move in opposite direction
        The body position and orientation is given by absolute pos and angle.
        If move is enabled, the legs are shifted by dPos = (dx,dy,dRz) each time
        """
        angle = map(lambda x: math.radians(x), angle) # angles from deg to rad

        # build body with desired position and orientation
        b, b2 = self.buildBody(pos, angle) 

        # if move, shift all feet position by dPos = (dx,dy,dRz) increment
        if move:
            self.setFeetPosInc(dPos)           

        # calculate body normal vector
        v0 = b[1] - b[0]
        v1 = b[2] - b[0]
        normal = np.cross(v0, v1)
        normal /= math.sqrt(np.dot(normal,normal))

        doMove = False

        """
        1 Cycle step = one leg move up or down
        Cycle steps = 12/MovingLegs
        if MovingLegs = 2
            Cycle:  Leg:     Vertical move:
            0       0 and 3      Up
            1       0 and 3      Down
            2       1 and 4      Up
            3       1 and 4      Down
            4       2 and 5      Up
            5       2 and 5      Down
            0       0 and 3      Up
            ...
        """
        # if legs movement enabled or some legs in the air, update legs position
        if move or (self.CycleStep % 2 == 1): 
            d = self.footDist 
            i = self.CycleStep/2

            for j in range(self.MovingLegs):  # reset the position of the legs which should move this cycle (1 to 3 legs)
                self.FootPos[i + j*6/self.MovingLegs] = [d*math.cos(self.bodyAngles[i + j*6/self.MovingLegs]),d*math.sin(self.bodyAngles[i + j*6/self.MovingLegs]),0]

            self.CycleStep += 1
            self.CycleStep %= (12/self.MovingLegs)

            if (self.CycleStep % 2 == 1):  # go up with the legs
                doMove = True

        # calculate inverse kinematics for each leg
        
        for i in range(6):
            f = self.FootPos[i]
            f_b = f - b[i]
            p = f - np.dot(normal, f_b)*normal  # x = (q - (n.(q-p))*n , q = out of plane, p = plane point, n = normal
            h0 = p - b[i]
            h1 = b2[i] - b[i]
            h0norm = math.sqrt(np.dot(h0,h0))
            h1norm = math.sqrt(np.dot(h1,h1))
            
            hipAngle = math.acos(np.dot(h0,h1)/h0norm/h1norm)

            k = b[i] + self.hip*h0/h0norm
            
            k_f = k-f
            kfnorm = math.sqrt(np.dot(k_f,k_f))  # norm
            
            x = (self.thigh**2 + self.foot**2 - kfnorm**2)/(2*self.thigh*self.foot)
            if -1 <= x <= 1:
                ankleAngle = math.acos(x)
            else:
                ankleAngle = np.nan

            bfnorm = math.sqrt(np.dot(f_b,f_b))  # norm

            x = (self.hip**2 + kfnorm**2 - bfnorm**2)/(2*self.hip*kfnorm)
            y = (self.thigh**2 + kfnorm**2 - self.foot**2)/(2*self.thigh*kfnorm)
            if -1 <= x <= 1 and -1 <= y <= 1:
                kneeAngle = math.acos(x) + math.acos(y)
            else:
                kneeAngle = np.nan
                
            # move proper legs up
            if doMove and (self.CycleStep / 2 == i % (6/self.MovingLegs)):
                kneeAngle += np.pi/5.0
                ankleAngle -= np.pi/5.0

            # send updated angles to servos only if solution exists
            if np.isnan((hipAngle, kneeAngle, ankleAngle)).any():
                print "No solution for leg %d" % i
            else:
                self.con.servos[self.Dict[i*3+0]].setPos(deg = int(-hipAngle/np.pi*180 + 90), move = False)
                self.con.servos[self.Dict[i*3+1]].setPos(deg = int(-kneeAngle/np.pi*180 + 180)*self.sign[i], move = False)
                self.con.servos[self.Dict[i*3+2]].setPos(deg = int(ankleAngle/np.pi*180 - 180 + ankleOffset)*self.sign[i], move = False)

        if send:
            self.con.sendBinary()

        


    











    
