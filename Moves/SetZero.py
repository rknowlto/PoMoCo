# Move: Set Zero

##for servo in hexy.con.servos:
##    hexy.con.servos[servo].setPos(deg=0)

hexy.con.servos[7].setPos(deg=0)
hexy.con.servos[6].setPos(deg=0)
hexy.con.servos[5].setPos(deg=ankleOffset)

hexy.con.servos[11].setPos(deg=0)
hexy.con.servos[10].setPos(deg=0)
hexy.con.servos[9].setPos(deg=ankleOffset)

hexy.con.servos[15].setPos(deg=0)
hexy.con.servos[14].setPos(deg=0)
hexy.con.servos[13].setPos(deg=ankleOffset)

if legsMirrored:
    aO = -ankleOffset
else:
    aO = ankleOffset
    
hexy.con.servos[16].setPos(deg=0)
hexy.con.servos[17].setPos(deg=0)
hexy.con.servos[18].setPos(deg=aO)

hexy.con.servos[20].setPos(deg=0)
hexy.con.servos[21].setPos(deg=0)
hexy.con.servos[22].setPos(deg=aO)

hexy.con.servos[24].setPos(deg=0)
hexy.con.servos[25].setPos(deg=0)
hexy.con.servos[26].setPos(deg=aO)
