from karl.v3 import*

def upDown():
    sleep(0.2)
    right_foot.angle(30)
    left_foot.angle(-30)
    sleep(0.2)
    right_foot.angle(-30)
    left_foot.angle(30)
    sleep(0.2)
    reset()
        
def up():
    sleep(0.2)
    right_foot.angle(55)
    left_foot.angle(-55)
    sleep(0.2)
    reset()
        
def down():
    sleep(0.2)
    right_foot.angle(-90)
    left_foot.angle(90)
    sleep(0.2)
    reset()
    
def shuffle():
    sleep(0.2)
    right_leg.angle(51)
    left_leg.angle(51)
    sleep(0.35)
    right_leg.angle(-51)
    left_leg.angle(-51)
    sleep(0.35)
    reset()

def wiggle():
    sleep(0.2)
    right_foot.angle(40)
    left_foot.angle(-40)
    sleep(0.2)
    sleep(0.2)
    right_leg.angle(30)
    left_leg.angle(30)
    sleep(0.2)
    right_leg.angle(-30)
    left_leg.angle(-30)
    sleep(0.2)
    reset()
    
def stepper():
    left_leg.angle(30)
    sleep(0.3)
    left_foot.angle(40)
    sleep(0.2)
    left_foot.angle(0)
    sleep(0.2)
    left_foot.angle(40)
    sleep(0.2)
    left_foot.angle(0)
    sleep(0.2)
    left_foot.angle(40)
    sleep(0.2)
    left_foot.angle(0)
    sleep(0.2)
    reset()
    
def totalerTanz():  
    up()
    down()  
    upDown()
    shuffle()
    wiggle()

#totalerTanz()

down()

upDown()

shuffle()

wiggle()

stepper()

#von Finjas (und "Emirkan")

    
