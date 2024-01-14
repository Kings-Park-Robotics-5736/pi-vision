import time
import typing

import cv2
import numpy

import app_contexts
import circle_score
import logger
import video_stream


def get_color_filter_mask(frame: numpy.ndarray, current_color_context: app_contexts.ColorContext):
    hsv = frame

    mask=None
    upper_red2 = numpy.array([current_color_context.red2.upper.h, current_color_context.red2.upper.s, current_color_context.red2.upper.v])
    lower_red2 = numpy.array([current_color_context.red2.lower.h, current_color_context.red2.lower.s, current_color_context.red2.lower.v])
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)

    upper_red1 = numpy.array([current_color_context.red1.upper.h, current_color_context.red1.upper.s, current_color_context.red1.upper.v])
    lower_red1 = numpy.array([current_color_context.red1.lower.h, current_color_context.red1.lower.s, current_color_context.red1.lower.v])
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)

    mask = mask1 | mask2 # type: ignore
  
    return mask

def find_circle_in_image(image_frame: video_stream.TimedFrame, app_context: app_contexts.AppContext) -> typing.Tuple[typing.Optional[numpy.ndarray], typing.Optional[video_stream.TimedFrame]]:
    try:
        start_time = time.time()
        if image_frame.frame is None:
            return None, image_frame

        mask = get_color_filter_mask(image_frame.frame, app_context.color_context)
        logger.debug("color filter time %d", time.time()-start_time)
        start_time = time.time()
        kernel = numpy.ones((10, 10), numpy.uint8)

        opening = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        median = cv2.medianBlur(opening,5)
        logger.debug("filters time %d", time.time()-start_time)
        start_time = time.time()
        edges = cv2.Canny(median, 100, 200)

        bigcircle=None
        circles = cv2.HoughCircles(edges, cv2.HOUGH_GRADIENT,
                                    dp=app_context.circle_context.dp, minDist=100,
                                    param1=app_context.circle_context.param1,
                                    param2=app_context.circle_context.param2,
                                    minRadius=10,maxRadius=200)
        logger.debug("hough time %d", time.time()-start_time)
        start_time = time.time()

        if circles is not None:
            circles = circle_score.filter_by_composite_score(edges, numpy.around(circles[0]), app_context.circle_context.circle_filter_b, app_context.circle_context.circle_filter_m)
            logger.debug("circle filter time %d", time.time()-start_time)
            start_time = time.time()
            circles = numpy.uint16(numpy.around(circles))
            counter=0
            big=0
            for circle in circles[0, :]:
                counter+=1

                if circle[2] >= big:
                    big = circle[2]
                    bigcircle = circle

        return bigcircle, image_frame

    except Exception:
        logger.exception("Unable to find circle")
        # just_the_string = traceback.format_exc()
        # print(just_the_string)
        # print(error)
    return None, None



def blobFilter(image_frame:numpy.ndarray, app_context: app_contexts.AppContext):
    params = cv2.SimpleBlobDetector_Params() 
        

    # Set Area filtering parameters 
    params.filterByArea = True
    params.minArea = app_context.circle_context.min_area
    params.maxArea = 10000

    # Set Circularity filtering parameters 
    params.filterByCircularity = True 
    params.minCircularity = app_context.circle_context.min_circularity
    params.maxCircularity = 1

    # Set Convexity filtering parameters 
    params.filterByConvexity = True
    params.minConvexity = app_context.circle_context.min_convexity

    # Set inertia filtering parameters 
    params.filterByInertia = True
    params.minInertiaRatio = app_context.circle_context.min_inertia
    params.filterByColor = False
    # Create a detector with the parameters 
    detector = cv2.SimpleBlobDetector_create(params) 
        
    # Detect blobs 
    keypoints = detector.detect(image_frame) 
    return keypoints

def find_image(image_frame: video_stream.TimedFrame, app_context: app_contexts.AppContext) -> typing.Tuple[typing.Optional[numpy.ndarray], typing.Optional[video_stream.TimedFrame]]:
    try:

       
        start_time = time.time()
        if image_frame.frame is None:
            logger.debug("Skipping empty image")
            return None, image_frame
        
        if(app_context.color_context.orientation == app_contexts.Orientation.UPSIDE_DOWN):
           image_frame = video_stream.TimedFrame( cv2.flip(image_frame.frame,-1), image_frame.time)

        mask = get_color_filter_mask(image_frame.frame, app_context.color_context)
        logger.debug("color filter time %d", time.time()-start_time)
        start_time = time.time()
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
        #kernel = numpy.ones((3, 3), numpy.uint8)
        #cv2.imshow("mask", image_frame.frame)
        #.waitKey()
        if( app_context.color_context.image_show == app_contexts.ImageShow.COLOR_FILTER):
            image_frame = video_stream.TimedFrame(mask, 200)


        opening = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        if( app_context.color_context.image_show == app_contexts.ImageShow.MORPHOLOGY):
            image_frame = video_stream.TimedFrame(opening, 200)

        median = cv2.medianBlur(opening,5)
        logger.debug("filters time %d", time.time()-start_time)
        start_time = time.time()

        if( app_context.color_context.image_show == app_contexts.ImageShow.MEDIAN_BLUR):
            image_frame = video_stream.TimedFrame(median, 200)


        #edges = cv2.Canny(median, 100, 200)
        #cv2.imshow("mask", edges)
        #cv2.waitKey() 
            
        ellipses = []

        contours, hierarchy = cv2.findContours(median, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        if(len(contours) ==0):
            return None, image_frame
        for c in contours: 
            #c = max(contours, key = cv2.contourArea)
            area = cv2.contourArea(c)
            if (area > 250):
                ellipse = cv2.fitEllipse(c)
                ellipses.append((c,ellipse))
                if(app_context.color_context.image_show == app_contexts.ImageShow.BLOB_AND_ELLIPSE):
                    cv2.ellipse(image_frame.frame, ellipse, (36,255,12), 2)
        
        if(len(ellipses) ==0):
            return None, image_frame

        keypoints = blobFilter(median,app_context)
        x=0
        y=0
        if len(keypoints) > 0:
            x,y =  keypoints[0].pt[0], keypoints[0].pt[1]
        
       
        if( app_context.color_context.image_show == app_contexts.ImageShow.BLOB_AND_ELLIPSE):
            blank = numpy.zeros((1, 1))  
            blob = cv2.drawKeypoints(image_frame.frame, keypoints, blank, (0, 0, 255), 
                            cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS) 
            image_frame = video_stream.TimedFrame(blob, 200)


        candidates = []
        if(x > 0 and y > 0):
            for contour, e in ellipses:
                (xc,yc),(d1,d2),angle = e
                result = cv2.pointPolygonTest(contour, (x,y), False) 
                if (result > 0):
                    candidates.append((contour,e))
        else:
            candidates = ellipses

        biggest_ellipse = candidates[0][1]
        biggest_contour_area = cv2.contourArea(candidates[0][0])
        for contour, ellipse in candidates:
            curr_contour = cv2.contourArea(contour)
            if curr_contour > biggest_contour_area:
                biggest_contour_area = curr_contour
                biggest_ellipse = ellipse

        return biggest_ellipse, image_frame

    except Exception:
        logger.exception("Unable to find circle")
        # just_the_string = traceback.format_exc()
        # print(just_the_string)
        # print(error)
    return None, None
