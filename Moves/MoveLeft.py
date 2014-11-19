import time
 
deg = -30
ankleDeg = 15
sleep = 0.3

hexy.LF.setFoot(footRx=ankleDeg)
hexy.LM.setFoot(footRx=ankleDeg)
hexy.LB.setFoot(footRx=ankleDeg)
hexy.RF.setFoot(footRx=-ankleDeg)
hexy.RM.setFoot(footRx=-ankleDeg)
hexy.RB.setFoot(footRx=-ankleDeg)
time.sleep(sleep)

hexy.LF.replantFoot(-deg,endAnkleAngle = -ankleDeg,stepTime=0.3)
hexy.RM.replantFoot(1,endAnkleAngle = ankleDeg,stepTime=0.3)
hexy.LB.replantFoot(deg,endAnkleAngle = -ankleDeg,stepTime=0.3)

time.sleep(sleep)

hexy.RF.replantFoot(deg,endAnkleAngle = ankleDeg,stepTime=0.3)
hexy.LM.replantFoot(1,endAnkleAngle = -ankleDeg,stepTime=0.3)
hexy.RB.replantFoot(-deg,endAnkleAngle = ankleDeg,stepTime=0.3)

time.sleep(sleep)

hexy.LF.setFoot(footRx=ankleDeg)
hexy.LM.setFoot(footRx=ankleDeg)
hexy.LB.setFoot(footRx=ankleDeg)
hexy.RF.setFoot(footRx=-ankleDeg)
hexy.RM.setFoot(footRx=-ankleDeg)
hexy.RB.setFoot(footRx=-ankleDeg)
time.sleep(sleep)

hexy.LF.replantFoot(-deg,endAnkleAngle = -ankleDeg,stepTime=0.3)
hexy.RM.replantFoot(1,endAnkleAngle = ankleDeg,stepTime=0.3)
hexy.LB.replantFoot(deg,endAnkleAngle = -ankleDeg,stepTime=0.3)

time.sleep(sleep)

hexy.RF.replantFoot(deg,endAnkleAngle = ankleDeg,stepTime=0.3)
hexy.LM.replantFoot(1,endAnkleAngle = -ankleDeg,stepTime=0.3)
hexy.RB.replantFoot(-deg,endAnkleAngle = ankleDeg,stepTime=0.3)

time.sleep(sleep)

hexy.LF.setFoot(footRx=ankleDeg)
hexy.LM.setFoot(footRx=ankleDeg)
hexy.LB.setFoot(footRx=ankleDeg)
hexy.RF.setFoot(footRx=-ankleDeg)
hexy.RM.setFoot(footRx=-ankleDeg)
hexy.RB.setFoot(footRx=-ankleDeg)
time.sleep(sleep)

hexy.LF.replantFoot(-deg,stepTime=0.3)
hexy.RM.replantFoot(1,stepTime=0.3)
hexy.LB.replantFoot(deg,stepTime=0.3)

time.sleep(sleep)

hexy.RF.replantFoot(deg,stepTime=0.3)
hexy.LM.replantFoot(1,stepTime=0.3)
hexy.RB.replantFoot(-deg,stepTime=0.3) 

