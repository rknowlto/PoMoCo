import time

# Move: Circle


hexy.RF.pointCircle(centerHipAngle=30,radius=10,orientation=1,stepTime=0.6)
hexy.LF.pointCircle(centerHipAngle=-30,radius=10,orientation=-1,stepTime=0.6)
time.sleep(0.6) 
hexy.RF.pointCircle(centerHipAngle=30,radius=20,orientation=1,stepTime=0.6)
hexy.LF.pointCircle(centerHipAngle=-30,radius=20,orientation=-1,stepTime=0.6)
time.sleep(0.6) 
hexy.RF.pointCircle(centerHipAngle=30,radius=30,orientation=1,stepTime=0.6)
hexy.LF.pointCircle(centerHipAngle=-30,radius=30,orientation=-1,stepTime=0.6)
time.sleep(0.6) 
hexy.RF.pointCircle(centerHipAngle=30,radius=30,orientation=-1,stepTime=0.6)
hexy.LF.pointCircle(centerHipAngle=-30,radius=30,orientation=1,stepTime=0.6)
time.sleep(0.6) 
hexy.RF.pointCircle(centerHipAngle=30,radius=20,orientation=-1,stepTime=0.6)
hexy.LF.pointCircle(centerHipAngle=-30,radius=20,orientation=1,stepTime=0.6)
time.sleep(0.6) 
hexy.RF.pointCircle(centerHipAngle=30,radius=10,orientation=-1,stepTime=0.6)
hexy.LF.pointCircle(centerHipAngle=-30,radius=10,orientation=1,stepTime=0.6)

