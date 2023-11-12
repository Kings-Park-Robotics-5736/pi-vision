import collections
import math
import os
import pathlib
import sys
import threading
import time
import typing

import cv2
import numpy

import app_contexts
import image_finder
import logger
import robot
import server
import shared_context
import video_stream


logger.setLevel(logger.INFO)


process_queue = collections.deque(maxlen=4)
# process_queue_lock = threading.Lock()
process_queue_condition = threading.Condition()
ready_queue = collections.deque(maxlen=4)
# ready_queue_lock = threading.Lock()
ready_queue_condition = threading.Condition()


def filter_frame(frame: numpy.ndarray):
    return cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)


def read_images(resolution: typing.Tuple[int, int] = (320, 240), fps: int = 30):
    global total_images_read
    for image in video_stream.transform_images(video_stream.get_images(resolution, fps), filter_frame):
        with process_queue_condition:
            process_queue.append(image)
            process_queue_condition.notify_all()


def process_images(app_context: app_contexts.AppContext):
    global total_images_processed
    while True:
        with process_queue_condition:
            while len(process_queue) == 0:
                process_queue_condition.wait()
            image_frame: video_stream.TimedFrame = process_queue.popleft()

        with ready_queue_condition:
            ready_queue.append(image_finder.find_image(image_frame, app_context))
            ready_queue_condition.notify_all()


def send_results(robot_connection: robot.RobotConnection, resolution: typing.Tuple[int, int] = (320, 240), last_seen: typing.Optional[shared_context.LastFrame] = None):
    half_h_fov = resolution[0]/2
    tan_h_fov = math.tan(.5427974) #half the HFOV degrees 31.1 to rad
    k = tan_h_fov/half_h_fov

    while True:
        with ready_queue_condition:
            while len(ready_queue) == 0:
                ready_queue_condition.wait()
            result = ready_queue.popleft()
            if not result:
                continue

            circle: numpy.ndarray = result[0]
            timed_frame: video_stream.TimedFrame = result[1]
            if last_seen and timed_frame:
                last_seen.set_frame_and_circle(timed_frame.frame, circle)
            if circle is None or len(circle) == 0:
                robot_connection.put_circle("SmartDashboard", None)
                continue

            x, y, radius = circle
            angle_x = math.atan((x - half_h_fov) * k) * 57.2958 #convert rad to deg
            robot_connection.put_circle("SmartDashboard", robot.CircleDefinition(
                x,
                y,
                radius,
                angle_x,
            ))


def main():
    process_threads = []
    thread_count = (os.cpu_count() or 4) - 1
    for i in range(0, thread_count):
        process_thread = threading.Thread(target=process_images, args=(shared_context.app_context,))
        process_thread.daemon = True
        process_thread.start()
        process_threads.append(process_thread)



    read_thread = threading.Thread(target=read_images, args=(shared_context.resolution, 30))
    read_thread.daemon = True
    read_thread.start()

    robot_connection = robot.RobotConnection("10.57.36.2", fake=False)
    robot_connection.connect()

    send_thread = threading.Thread(target=send_results, args=(robot_connection, shared_context.resolution, shared_context.last_seen))
    send_thread.daemon = True
    send_thread.start()
    # send_results(robot_connection, shared_context.resolution, shared_context.last_seen)

    server.start_server()


if __name__ == "__main__":
    main()
