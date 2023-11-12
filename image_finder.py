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
    if current_color_context.team == app_contexts.TeamColor.RED:
        upper_red2 = numpy.array([current_color_context.red2.upper.h, current_color_context.red2.upper.s, current_color_context.red2.upper.v])
        lower_red2 = numpy.array([current_color_context.red2.lower.h, current_color_context.red2.lower.s, current_color_context.red2.lower.v])
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)

        upper_red1 = numpy.array([current_color_context.red1.upper.h, current_color_context.red1.upper.s, current_color_context.red1.upper.v])
        lower_red1 = numpy.array([current_color_context.red1.lower.h, current_color_context.red1.lower.s, current_color_context.red1.lower.v])
        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)

        mask = mask1 | mask2 # type: ignore
    else:
        upper_blue = numpy.array([current_color_context.blue.upper.h, current_color_context.blue.upper.s, current_color_context.blue.upper.v])
        lower_blue = numpy.array([current_color_context.blue.lower.h, current_color_context.blue.lower.s, current_color_context.blue.lower.v])

        mask = cv2.inRange(hsv, lower_blue, upper_blue)
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

def find_image(image_frame: video_stream.TimedFrame, app_context: app_contexts.AppContext) -> typing.Tuple[typing.Optional[numpy.ndarray], typing.Optional[video_stream.TimedFrame]]:
    try:
        start_time = time.time()
        if image_frame.frame is None:
            return None, image_frame

        mask = get_color_filter_mask(image_frame.frame, app_context.color_context)
        logger.debug("color filter time %d", time.time()-start_time)
        start_time = time.time()
        kernel = numpy.ones((10, 10), numpy.uint8)
        #cv2.imshow("mask", image_frame.frame)
        #.waitKey()

       # image_frame = mask
        opening = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        median = cv2.medianBlur(opening,5)
        logger.debug("filters time %d", time.time()-start_time)
        start_time = time.time()


        #edges = cv2.Canny(median, 100, 200)
        #cv2.imshow("mask", edges)
        #cv2.waitKey()

        contours, hierarchy = cv2.findContours(median, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        if(len(contours) ==0):
            return None, None
        c = max(contours, key = cv2.contourArea)

        M = cv2.moments(c)
        cx = int(M['m10']/M['m00'])
        cy = int(M['m01']/M['m00'])

        bigcircle=(cx, cy, .01)
        """
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
        """
        return bigcircle, image_frame

    except Exception:
        logger.exception("Unable to find circle")
        # just_the_string = traceback.format_exc()
        # print(just_the_string)
        # print(error)
    return None, None
