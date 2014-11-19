import time
import math
import serial
import serial.tools.list_ports
import threading

debug = False
startTime = time.clock()
serialSends = []

BAUD_RATE = 9600
CENTER = 1500 # 1400 for TURNIGY TGY 50090M (default = 1500)
GAIN = 11.111  # 10.01 for TURNIGY TGY 50090M (default = 11.111) (do not use 10.0 - python will assume int instead of float)

class runMovement(threading.Thread):

    def __init__(self,function,*args):
        threading.Thread.__init__(self)
        self.function=function
        self.args = args
        self.start()

    def run(self):
        self.function(*self.args)

class serHandler(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

        self.ser = None

        self.sendQueue=[]
        self.sendLock = threading.Lock()

        self.recieveQueue=[]
        self.recieveLock = threading.Lock()

        self.serOpen = False
        self.serNum = 0

        self.start()

    def __del__(self):
        self.ser.close()

    def run(self):
        self.connect()
        while(True):
            # Send waiting messages
            send = False
            if(len(self.sendQueue)>0):
                self.sendLock.acquire()
                toSend = self.sendQueue.pop(0)
                self.sendLock.release()
                send = True
            else:
                time.sleep(0.01) # Keeps infinite while loop from killing processor
            if send:
                sendTime = time.clock()-startTime
                serialSends.append([float(sendTime),str(toSend)])
                time.sleep(0.003)
                if self.serOpen:
                    if self.ser.writable:
                        if self.serOpen:
                            self.ser.write(str(toSend))
##                            print "Sent '%s' to COM%d"%(str(toSend).strip('\r'),self.serNum+1)
            if debug:
                print "Sent '%s' to COM%d"%(str(toSend).strip('\r'),self.serNum+1)

## work in progress
            # Retrieve waiting responses
            # TODO: Don't need reading yet, holding off on fully implementing it till needed.
            if self.ser.readable():
                read = self.ser.readline()
                if len(read) == 0:
                    pass
##                    print "derp"
                else:
##                    print "recieved %s from COM %d"%(str(read),self.serNum+1)
                    print read
                    self.recieveLock.acquire()
                    self.recieveQueue.append(read)
                    self.recieveLock.release()
            

    def connect(self):
            comList = []
            comports = serial.tools.list_ports.comports()
            for comport in comports:
                    for thing in comport:
                            #print thing
                            comList.append(thing)
            
            comList = list(set(comList))
            print comList
                
            print "Attempting to connect to Servotor"
            for port in comList:
                    try:
                            ser = serial.Serial(port, baudrate= BAUD_RATE, timeout=2)
                            ser.write('V\n')
                            result = ser.readline()
                            if "SERVOTOR" in result:
                                    print "Connect Successful! Connected on port:",port
                                    self.ser = ser
                                    self.ser.flush()
                                    self.serOpen = True
                                    self.serNum = 1
                                    break
                    except:
                            pass
            
            if self.serOpen == False:
                print "Trying Windows Method"
                for i in range(0,30):
                    try:
                        try:
                            ser = serial.Serial(i, baudrate = BAUD_RATE, timeout = 0.005) # found important to set timeout very small, it influences update time of serial.read 
                            print "ser",i
                        except:
                            print "ser",i,"failed"
                            raise Exception
                        ser.flush()
                        time.sleep(0.1)
                        ser.write("V\n")
                        time.sleep(1)
                        readReply = ser.readline()
                        #print "read:",readReply
                        if "SERVOTOR" in readReply:
                            print "Connect Successful! Connected on port COM"+str(i+1)
                            ser.flush()
                            self.ser = ser
                            self.serNum = i
                            self.serOpen = True
                            break
                        else:
                            ser.close()
                            pass
                    except:
                        pass
                    
class Servo:

    def __init__(self,servoNum,serHandler,servoPos=CENTER,active=False):
        self.serHandler = serHandler
        self.active = active
        self.servoNum = servoNum

        # Servo position and offset is stored in microseconds (uS)
        self.servoPos = servoPos
        self.offset = [0,0,0,0,0,0,0]


    def setPos(self, timing=None, deg=None, move=True):
        if timing != None:
            self.servoPos = timing
        if deg != None:
            self.servoPos = int(CENTER+float(deg)*GAIN)
        if move:
            self.active = True
            self.move()
            if debug: print "Moved ",self.servoNum
        if debug: print "Servo",self.servoNum,"set to",self.servoPos

    def getPosDeg(self):
        return (self.servoPos-CENTER)/GAIN

    def getPosuS(self):
        return self.servoPos

    def getActive(self):
        return self.active

    def getOffsetDeg(self, index = 3):
        return self.offset[index]/GAIN

    def getOffsetuS(self, index = 3):
        return self.offset[index]

    def setOffset(self, timing=None, deg=None,index = 3):
        if timing != None:
            self.offset[index] = timing
        if deg != None:
            self.offset[index] = int(float(deg)*GAIN)

    def calculateOffset(self, pos):
        if pos < (CENTER-80*GAIN):
            newServoPos = pos + self.offset[0]
        elif pos < (CENTER-60*GAIN):
            newServoPos = pos + int((self.offset[1]-self.offset[0])*(pos-(CENTER-80*GAIN))/(20*GAIN) + self.offset[0])
        elif pos < (CENTER-30*GAIN):
            newServoPos = pos + int((self.offset[2]-self.offset[1])*(pos-(CENTER-60*GAIN))/(30*GAIN) + self.offset[1])
        elif pos < CENTER:
            newServoPos = pos + int((self.offset[3]-self.offset[2])*(pos-(CENTER-30*GAIN))/(30*GAIN) + self.offset[2])
        elif pos < (CENTER+30*GAIN):
            newServoPos = pos + int((self.offset[4]-self.offset[3])*(pos-CENTER)/(30*GAIN) + self.offset[3])
        elif pos < (CENTER+60*GAIN):
            newServoPos = pos + int((self.offset[5]-self.offset[4])*(pos-(CENTER+30*GAIN))/(30*GAIN) + self.offset[4])
        elif pos < (CENTER+80*GAIN):
            newServoPos = pos + int((self.offset[6]-self.offset[5])*(pos-(CENTER+60*GAIN))/(20*GAIN) + self.offset[5])
        else:
            newServoPos = pos + self.offset[6]
    
        return newServoPos

    def reset(self):
        self.setPos(timing=CENTER)
        self.move()

    def kill(self):
        self.active = False
        toSend = "#%dL\r"%(self.servoNum)
        self.serHandler.sendLock.acquire()
        self.serHandler.sendQueue.append(toSend)
        self.serHandler.sendLock.release()
        if debug: print "Sending command #%dL to queue"%self.servoNum

    def move(self):
        if self.active:
            servoPos = self.calculateOffset(self.servoPos)
            # Auto-correct the output to bound within 500uS to 2500uS signals, the limits of the servos
            if servoPos < 500:
                servoPos = 500
            if servoPos > 2500:
                servoPos = 2500
                
            # Debug message if needed
            if debug: print "Sending command #%dP%dT0 to queue"%(self.servoNum,int(servoPos))

            # Send the message the serial handler in a thread-safe manner
            toSend = "#%dP%.4dT0\r"%(self.servoNum,int(servoPos))
            self.serHandler.sendLock.acquire()
            self.serHandler.sendQueue.append(toSend)
            self.serHandler.sendLock.release()
        else:
            try:
                toSend = "#%.4dL\r"%(self.servoNum,int(servoPos))
                self.serHandler.sendLock.acquire()
                self.serHandler.sendQueue.append(toSend)
                self.serHandler.sendLock.release()
                if debug: print "Sending command #%dL to queue"%self.servoNum
            except:
                pass

class Controller:
    def __init__(self,servos=32):
        self.Dict = [5,6,7, 9,10,11, 13,14,15, 16,17,18, 20,21,22, 24,25,26, 31]
        self.serialHandler = serHandler()
        timeout = time.time()
        while not (self.serialHandler.serOpen or (time.time()-timeout > 1.0)):
            time.sleep(0.01)
        if self.serialHandler.serOpen == False:
            print "Connection to Servotor failed. No robot movement will occur."
        print "Initializing servos."
        self.servos = {}
        for i in range(32):
            self.servos[i]=Servo(i,serHandler=self.serialHandler)
            self.servos[i].kill()

        print "Servos initialized."
        
    def sendBinary(self):
        toSend = '$'
        for i in range(len(self.Dict)):   # 19 servos with fixed order (see self.Dict), if modified, then also in Servotor32
            servoPos = self.servos[self.Dict[i]].getPosuS()
            servoPos = self.servos[self.Dict[i]].calculateOffset(servoPos)
            if servoPos < 500:  servoPos = 500
            if servoPos > 2500: servoPos = 2500
            toSend += chr(int(round(servoPos/10.0)))  #using int(round()) because int() works like floor() which is not good rounding
        toSend += '\r'
        self.serialHandler.sendLock.acquire()
        self.serialHandler.sendQueue.append(toSend)
        self.serialHandler.sendLock.release()
##        print "sent: ", toSend
        
    def __del__(self):
        del self.serialHandler

    def killAll(self):
        if self.serialHandler.serOpen:
##            for servo in self.servos:
##                self.servos[servo].kill()
            self.serialHandler.sendLock.acquire()
            self.serialHandler.sendQueue.append("K")
            self.serialHandler.sendLock.release()    
        print "Killing all servos."

if __name__ == '__main__':
    pass
    conn = Controller()
