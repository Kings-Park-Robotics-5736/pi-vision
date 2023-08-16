import cv2 as cv
import cv2
import numpy as np
import traceback
from VisionServer import getAttribute, getImageFile,startServer
#from networktables import NetworkTables
import time
from circleScore import getCompositeScore, filterByCompositeScore
from videoStream import PiVideoStream
import os
#onrobot=True
onrobot=False
view=False
from pipeline import Pipeline
import math
from threading import Semaphore
import threading
mutex=Semaphore(1)

resultArray=[]
condition = threading.Condition()
#lastFrameTime=time.time()
maxSize=4
lastTime = time.time()

total_frames_processed = 0
start_time = time.time()
def onResults(bigCircleTime):
        global condition, total_frames_processed, start_time
        #global lastFrameTime
        with condition:
                resultArray.append(bigCircleTime)
                if len(resultArray) >= maxSize:
                        resultArray.pop()
                total_frames_processed += 1
                if time.time() - start_time > 10:
                        print(f"processed: {total_frames_processed}")
                        start_time = time.time()
                        total_frames_processed = 0
                condition.notify_all()
                #print(time.time()-lastFrameTime)
                #lastFrameTime = time.time()


if onrobot:
    while True:
        hostname = "10.57.36.2"
        response = os.system("ping -c 1 " + hostname)
        if response == 0:
                print (hostname, 'is up!')
                break
        else:
                time.sleep(1)
                print("Waiting for connection")

    NetworkTables.initialize(server='10.57.36.2')
    sd = NetworkTables.getTable("SmartDashboard")
#print(sd)

startServer()
vs = PiVideoStream().start()
#cap = cv2.VideoCapture(0)
#cap.set(cv.CAP_PROP_FRAME_HEIGHT, 240)
#cap.set(cv.CAP_PROP_FRAME_WIDTH, 360)
loopCounter=0


threads=[]
for i in range(0,4):
        threads.append(Pipeline(vs, onResults).start())
        time.sleep(0.016)

halfHFOV = vs.getResolution()[0]/2
tanHFOV = math.tan(.5427974) #half the HFOV degrees 31.1 to rad
K=tanHFOV/halfHFOV
results = 0
start=time.time()
while(1):
    # Take each frame
    loopCounter+=1
    try:

        if (time.time()-start)>3:
                results =0
                start = time.time()
        bigcircle=None
        with condition:
                while len(resultArray)==0:
                        condition.wait()
                results+=1
                #print(results/(time.time()-start))
                bigcircle, frameTime =resultArray.pop(0)

                if frameTime < lastTime:
                        continue
                lastTime = frameTime
                #resultArray=[]
        if bigcircle is not None:
                x, y, radius = bigcircle
                center = (x, y)
                angleX = math.atan(K*(x-halfHFOV))*57.2958 #convert rad to deg
                if onrobot:
                #print(bigcircle)
                    sd.putNumber("centerx", center[0])
                    sd.putNumber("centery", center[1])
                    sd.putNumber("radius", radius)
                    sd.putNumber("anglex", angleX)


        else:
            if onrobot:
                sd.putNumber("centerx", -1)
                sd.putNumber("centery", -1)
                sd.putNumber("radius", -1)
                sd.putNumber("anglex", -1)
            else:
                pass

        frame = vs.readAny()


        if bigcircle is not None:
                        x, y, radius = bigcircle;
                        cv2.circle(frame, center, radius, (0, 255, 0), 5);
            #res = cv.bitwise_and(frame, frame, mask=median)
        if view:
            cv.imshow('frame',frame)
            k = cv.waitKey(5) & 0xFF
            if k == 27:
                break

        #print("pre-write=",time.time()-start)
        cv.imwrite(getImageFile(), frame)

        #print("end=",time.time()-start)


    except Exception as error:
        just_the_string = traceback.format_exc()
        print(just_the_string)
        print(error)

cv.destroyAllWindows()
