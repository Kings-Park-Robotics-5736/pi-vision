import cv2 as cv
import cv2
import numpy as np
import traceback
from VisionServer import getAttribute, getImageFile,startServer
#from networktables import NetworkTables
import time
from circleScore import getCompositeScore, filterByCompositeScore
from videoStream import PiVideoStream
from threading import Thread, Semaphore

import os
printTimings =False
view = False
class Pipeline:
        def __init__(self, vs, resultCallback ):
                self.vs = vs
                vs.setImageFilter(self.convertColor)
                self.resultCallback = resultCallback
                
        def start(self):
                Thread(target=self.runpipeline, args=()).start()
                return self
                        
        def convertColor(self, frame):
                return cv.cvtColor(frame, cv.COLOR_BGR2HSV)
                
        def filterByColor(self, frame):
                hsv = frame#self.convertColor(frame)
                
                mask=None
                # define range of blue color in HSV
                # the frist rnge
                # lower_red2 = np.array([170,150,100])
                # upper_red2 = np.array([180,255,255])
                # Threshold the HSV image to get only blue colors
                
                if getAttribute("team-color", 'String') =='Red':
                        upper_red2 = np.array([getAttribute("HRedUpper2"),getAttribute("SRedUpper2"),getAttribute("VRedUpper2")])
                        lower_red2 = np.array([getAttribute("HRedLower2"), getAttribute("SRedLower2"), getAttribute("VRedLower2")])

                        mask2 = cv.inRange(hsv, lower_red2, upper_red2)


                      #  lower_red1 = np.array([0,90,100])
                       # upper_red1 = np.array([12,255,255])
                        upper_red1 = np.array([getAttribute("HRedUpper1"),getAttribute("SRedUpper1"),getAttribute("VRedUpper1")])
                        lower_red1 = np.array([getAttribute("HRedLower1"), getAttribute("SRedLower1"), getAttribute("VRedLower1")])
                        # Threshold the HSV image to get only blue colors
                        mask1 = cv.inRange(hsv, lower_red1, upper_red1)
                        mask=mask1 | mask2

             #   lower_blue = np.array([95,75,20])
              #  upper_blue = np.array([115,255,255])
                else:
                        upper_blue = np.array([getAttribute("HBlueUpper1"),getAttribute("SBlueUpper1"),getAttribute("VBlueUpper1")])
                        lower_blue = np.array([getAttribute("HBlueLower1"), getAttribute("SBlueLower1"), getAttribute("VBlueLower1")])
                        # Threshold the HSV image to get only blue colors
                        mask = cv.inRange(hsv, lower_blue, upper_blue)
                return mask
        def runpipeline(self):
                
           while True:
             try:
                start = time.time()
                frame, frameTime = self.vs.read()
                #print(frame)
                if  frame is None:
                        continue 
                mask = self.filterByColor(frame)

                # Bitwise-AND mask and original image

                #mask = mask1|mask2|mask3
                if printTimings:
                        print("color filter=",time.time()-start)
                kernel = np.ones((10, 10), np.uint8)
                opening = cv.morphologyEx(mask, cv.MORPH_OPEN, kernel)


                median = cv.medianBlur(opening,5)
                if printTimings:
                        print("filters=", time.time()-start)
                edges = cv.Canny(median, 100, 200)
                
                bigcircle=None
                # start=time.time()
                circles = cv2.HoughCircles(edges, cv2.HOUGH_GRADIENT, 
                                           dp=getAttribute("dp"), minDist=100, 
                                           param1=getAttribute("p1"), param2=getAttribute("p2"),
                                           minRadius=10,maxRadius=200)
                if printTimings:
                        print("hough=",time.time()-start)
                if circles is not None:
                    circles = filterByCompositeScore(edges, np.around(circles[0]), getAttribute("fp1"), getAttribute("fp2"))
                    if printTimings:
                        print("circlefilter=",time.time()-start)
                    # round to ints
                    circles = np.uint16(np.around(circles));
                    counter=0
                    big=0
                    for circle in circles[0, :]:
                        counter+=1

                        if circle[2] >= big:
                            big = circle[2]
                            bigcircle = circle
                #if printTimings:
                #print("end=",time.time()-start)
                
                if view:
                    res = cv.bitwise_and(frame, frame, mask=median)
                    #cv.imshow('frame',frame)
                    cv.imshow('mask',mask)
                    cv.imshow('res',res)
                    cv.imshow('blur', median)
                    cv.imshow('open', opening)
                    cv.imshow('edges', edges)
                    k = cv.waitKey(5) & 0xFF
                    if k == 27:
                        break
                self.resultCallback((bigcircle, frameTime))
             except Exception as error:
                just_the_string = traceback.format_exc()
                print(just_the_string)
                print(error)

