

import math
import cv2 as cv
import numpy as np
from timeit import default_timer as timer

#for a given point, check if it is inside our circle
def isInside(circle_x, circle_y, rad, x, y):

    # Compare radius of circle
    # with distance of its center
    # from given point
    if ((x - circle_x) * (x - circle_x) +
        (y - circle_y) * (y - circle_y) <= rad * rad):
        return True
    else:
        return False

def pixelIterate(img, circle, index):
    h = img.shape[0]
    w = img.shape[1]

    circleScore = 0
    circlePoint=0
    # loop over the image, pixel by pixel
    for y in range(max(circle[1]-circle[2],0),min(circle[1]+circle[2],h )):
        for x in range(max(circle[0]-circle[2],0),min(circle[0]+circle[2],w)):

                if img[y, x] >0:

                    res = True #isInside(circle[0], circle[1], circle[2]+3, x,y)
                    if res:
                        sum=circle[2]-math.sqrt((circle[0]-x)*(circle[0]-x) + (circle[1]-y)*(circle[1]-y))
                        circleScore+=abs(sum)
                        circlePoint+=1
    return (circleScore, circlePoint)


def wideCheck(xi, yi, expand, img):
    for xip in range(xi-expand, xi+expand+1):
            for yip in range(yi-expand, yi+expand+1):
                if xip<img.shape[1] and yip < img.shape[0]:
                    if img[yip, xip]>0:
                        return True
    return False


#Get the Miroslav score for a circle
#Returns a score for each circle in a range from 0-100
#Computes how well the pixel circumferences follows the ideal circumference
def getMiroslavScore(img, circles):

    result=np.zeros(len(circles), np.uint8)
    fi=np.linspace(0,2*math.pi, endpoint=False,  num=100)
    for c in range(0,len(circles)):
        sum=0
        for i in range(1,100):
            xi=circles[c][0]+round(circles[c][2]*math.cos(fi[i]))
            yi=circles[c][1]+round(circles[c][2]*math.sin(fi[i]))

            sum+=1 if  wideCheck(xi, yi, 3, img) else 0
        result[c]=sum
    return result

#Get the Barish score for a circle
#Returns scores from 0 - inf
#computes how well the pixels are close to the circumference

def getBarishScore(img, circles):
    circleScores=np.zeros(len(circles), np.uint32)
    circlePoints=np.zeros(len(circles), np.uint32)

    for i in range(0,len(circles)):
        ret,thresh1 = cv.threshold(img,5,1,cv.THRESH_BINARY)
        img_black = np.zeros((img.shape[0],img.shape[1]), np.uint8)


        circle=cv.circle(img_black, (circles[i][0], circles[i][1]), int(3*(circles[i][2]/4)),int((circles[i][2]/4)) ,-1)
        circle=cv.circle(circle, (circles[i][0], circles[i][1]), int((circles[i][2]/2)),int((circles[i][2]/2)) ,-1)
        circle=cv.circle(circle, (circles[i][0], circles[i][1]),int((circles[i][2]/4)),int(3*(circles[i][2]/4)) ,-1)

        final_image = np.multiply(thresh1 , circle)
        circleScores[i] = np.sum(final_image)


        circle_all=cv.circle(img_black, (circles[i][0], circles[i][1]), circles[i][2]+5, 1,-1)
        points = np.count_nonzero(np.logical_and(thresh1, img_black))
        circlePoints[i]=points if points > 0 else 1


    return np.divide(circleScores,circlePoints)
    #return circleScores


#Get the barish and miroslav scores for a list of circles
def getCompositeScore(img, circles):
    kernel = np.ones((5,5), np.uint8)

    img_dilation = cv.dilate(img, kernel, iterations=1)
    return (getBarishScore(img_dilation, circles),getMiroslavScore(img, circles))


#Get a new list of circles that have been filtered by the thresholds
#bScoreThresh should be bigger than the value
#mScoreThresh should be smaller than the value
def filterByCompositeScore(img, circles, bScoreThresh, mScoreThresh):

    kernel = np.ones((5,5), np.uint8)
    circles=circles.astype(int)
    #img_dilation = cv.dilate(img, kernel, iterations=1)



    retListFinal=[]
    retList=[]
    bScore = getBarishScore(img, circles)
    #print(bScore)

    for i in range(0, len(circles)):
        if  bScore[i] <=bScoreThresh:
            retList+=[circles[i]]

    mScore = getMiroslavScore(img, retList)
    #print(mScore)
    for i in range(0, len(retList)):
        if  mScore[i] >=mScoreThresh:
            retListFinal+=[retList[i]]


    return [retListFinal]
