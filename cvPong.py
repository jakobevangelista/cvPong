import sys
import cv2 #make sure to install cv2 on python
import numpy as np
import RPi.GPIO as GPIO
import time
import random

# open video camera
cap = cv2.VideoCapture(0)
 
# define objects for impact detection and displaying
# x, y, w, h, color
leftPaddle = [2, 29, 2, 12, 7]
rightPaddle = [60, 29, 2, 12, 7]
ball = [31, 31, 2, 2, 1]

# dx, dy
ballMovement = [0, 0]
ballSpeed = 0.5

screen = np.zeros([64, 64], dtype=int)

# score vals
leftPlayer = 0
rightPlayer = 0
 
#setup output pins for LED Matrix
# pins in order
# R1, B1, R2, B2, HA, HC, CLK, OE, G1, GND, G2, HE, HB, HD, LAT, GND
R1 = 4
B1 = 17
R2 = 27
B2 = 22
HA = 5 
HC = 6 
CLK= 13 
OE = 19
G1 = 26
G2 = 18
HD = 23
HE = 24
HB = 25 
LAT= 12

pins = [R1, B1, R2, B2, HA, HC, CLK, OE, G1, G2, HD, HE, HB, LAT]
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
for pin in pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, 0)

delay = 0.00000005 # 1.5 microseconds

def bitsFromInt(x):
    a = bool(x & 1)
    b = bool(x & 2)
    c = bool(x & 4)
    d = bool(x & 8)
    e = bool(x & 16)
    return (a, b, c, d, e)

def setRow(row):
    a, b, c, d, e = bitsFromInt(row)
    GPIO.output(HA, a)
    GPIO.output(HB, b)
    GPIO.output(HC, c)
    GPIO.output(HD, d)
    GPIO.output(HE, e)

def setColorBottom(color):
    r, g, b, x, y = bitsFromInt(color)
    GPIO.output(R2, r)
    GPIO.output(G2, g)
    GPIO.output(B2, b)
    
def setColorTop(color):
    r, g, b, x, y = bitsFromInt(color)
    GPIO.output(R1, r)
    GPIO.output(G1, g)
    GPIO.output(B1, b)

#only have to manage white and black colors
def fillRectangle(x1, y1, x2, y2, color):
    for x in range(x1, x2):
        for y in range(y1, y2):
            screen[y][x] = color

def init():
    GPIO.output(CLK, 0)
    GPIO.output(OE, 1)
    GPIO.output(LAT, 0)
    
    # calc ball movement
    dx = random.uniform(-1, 1)
    dy = random.uniform(-1, 1)
    
    magnitude = np.sqrt(dx**2 + dy**2)
    ballMovement[0] = dx * ballSpeed / magnitude
    ballMovement[1] = dy * ballSpeed / magnitude
    
    # ensure the ball goes mostly left-right
    if abs(dy / dx) > 2:
        init()
    
def clearScreen():
    for i in range(64):
        for j in range(64):
            screen[i][j] = 0

def fillScreen(obj):
    # objects are in format:
    # x, y, w, h, color
    a = int(max(obj[0], 0))
    b = int(min(obj[0] + obj[2], 64))
    
    c = int(max(obj[1], 0))
    d = int(min(obj[1] + obj[3], 64))
    
    for i in range(a, b):
        for j in range(c, d):
            screen[j][i] = obj[4]

def customSleep(duration):
    #busy loop for the duration instead of trying to sleep for that long...
    start = time.time()
    while True:
        current = time.time()
        if current - start > duration:
           break

def displayScreen():
    for r in range(32):
        GPIO.output(OE, 1) # turn off row of LEDs
        setRow(r) # select row to output data to
        for c in range(64):
            setColorTop(screen[r][c])
            setColorBottom(screen[r + 32][c])
            GPIO.output(CLK, 1)
            customSleep(delay) #pulse the clock
            GPIO.output(CLK, 0)
        
        GPIO.output(LAT, 1) # end row write
        customSleep(delay)
        GPIO.output(LAT, 0) # enable row writes
        GPIO.output(OE, 0) # activate row LEDs
        customSleep(delay * 1000) # let the row flash its color
        GPIO.output(OE, 1)

cascade_file = cv2.CascadeClassifier("fist.xml")
init()
count = 0
while True:
    if count % 4 == 0:
        _, frame = cap.read()
        height1, width1, channels1 = frame.shape
        frame_resize1 = frame[0:height1, 0:int(width1/2)]
        grayimage = cv2.cvtColor(frame_resize1, cv2.COLOR_RGB2GRAY)
        fist = cascade_file.detectMultiScale(grayimage,scaleFactor=1.05, minNeighbors=4, minSize=(30, 30))
                
        frame_resize2 = frame[0:height1, int(width1/2):width1]
        grayimage2 = cv2.cvtColor(frame_resize2, cv2.COLOR_RGB2GRAY)
        fist2 = cascade_file.detectMultiScale(grayimage2,scaleFactor=1.05, minNeighbors=4,minSize=(30, 30))

        halfFrameHeight = height1 / 2
    
        for x, y, w, h in fist2:
            #k = cv2.rectangle(frame_resize1, (x, y), (x + w, y + h), (255, 255, 255), 5)
            leftYPos = (y - halfFrameHeight) / 7 + 27
            leftPaddle[1] = max(0, min(leftYPos, 52))
            
            #override left fist detection
            #leftPaddle[1] = ball[1] - 5
            print(leftYPos + 6, " left fist pos")

        for x, y, w, h in fist:
            #k = cv2.rectangle(frame_resize2, (x, y), (x + w, y + h), (255, 255, 255), 5)
            rightYPos = (y - halfFrameHeight) / 7 + 27
            rightPaddle[1] = max(0, min(rightYPos, 52))
            print(rightYPos + 6, " right fist pos")

    ball[0] += ballMovement[0]
    ball[1] += ballMovement[1]
    #cap.set(3,640)
    #cap.set(4,480)
    #cv2.imshow("vid",frame)
    
    # check boundaries
    
    # out of bounds
    if ball[0] < -1 or ball[0] > 64:
        #reset ball
        ball[0] = 31
        ball[1] = 31
        init()
    
    # bounce off of top and bottom
    if ball[1] < 1 or ball[1] > 62:
        ballMovement[1] = ballMovement[1] * -1

    # bounce off of left paddle
    if ball[0] - leftPaddle[0] < 2 and ball[1] - leftPaddle[1] > 0 and ball[1] - leftPaddle[1] < rightPaddle[3]:
        ballMovement[0] = abs(ballMovement[0])
    
    # bounce off of right paddle
    if rightPaddle[0] - ball[0] < 2 and ball[1] - rightPaddle[1] > 0 and ball[1] - rightPaddle[1] < rightPaddle[3]:
        ballMovement[0] = -abs(ballMovement[0])

    clearScreen()    
    fillScreen(leftPaddle)
    fillScreen(rightPaddle)
    fillScreen(ball)
    displayScreen()
    count = count + 1

# first problem we ran into is connecting the game and tracking software
# then we didnt know how to track 2 different items of the same object
# tried to make our own haar cascade file
# then we tried tracking 2 different objects, hand detection too similar, even tried manually training xml
# then we split the screen in 2 to track left and right Player1
# then we had to make a function to control the paddle since coordinates not similar
# has to be solid color background

