import typing

import ntcore
import video_stream
import numpy
import cv2

from cscore import CameraServer

class CircleDefinition:
    x: float
    y: float
    radius: float
    anglex: float

    def __init__(self, x: float, y: float, radius: float, anglex: float):
        self.x = x
        self.y = y
        self.radius = radius
        self.anglex = anglex

class EllipseDefinition:
    x: float
    y: float
    d1: float
    d2:float
    theta:float
    anglex: float

    def __init__(self, x: float, y: float, d1: float, d2:float, theta:float, anglex: float):
        self.x = x
        self.y = y
        self.d1 = d1
        self.d2 = d2
        self.theta = theta
        self.anglex = anglex


class RobotConnection:
    def __init__(self, robot_ip: str, fake: bool=False):
        self.robot_ip = robot_ip
        self.fake = fake

        

    def connect(self):
        if self.fake:
            self.nt = ntcore.NetworkTableInstance.startTestMode()
            pass
        else:
            self.nt = ntcore.NetworkTableInstance.getDefault()
            self.nt.startClient4("wpilibpi")
            self.nt.setServerTeam(5736)
            self.nt.startDSClient()

            #networktables.NetworkTables.initialize(server=self.robot_ip)
            #CameraServer.startAutomaticCapture()
            self.outputStream = CameraServer.putVideo("Processed", 320, 240)

    def get_table(self, table_name: str) -> ntcore.NetworkTable:
        return self.nt.getTable(table_name)

    def put_number(self, table_name: str, key: str, value: float):
        self.get_table(table_name).putNumber(key, value)


    def sendFrame(self, timed_frame: video_stream.TimedFrame, ellipse: numpy.ndarray ):
        if not timed_frame or not len(timed_frame.frame) or not numpy.any(timed_frame.frame):
            return 
        frame = None
        if timed_frame.frame.ndim >2:
            frame = cv2.cvtColor(timed_frame.frame, cv2.COLOR_HSV2BGR)
        else:
            frame = timed_frame.frame
        if ellipse:
            cv2.ellipse(frame, ellipse, (36,255,12), 2)
            cv2.circle(frame, (int(ellipse[0][0]), int(ellipse[0][1])), int(2), (0, 255, 0), 2)
        #print("Sending Frame", flush=True)
        self.outputStream.putFrame(frame)

    def put_circle(self, table_name: str, circle: typing.Optional[CircleDefinition]):
        if circle is None:
            self.put_number(table_name, "centerx", -1)
            self.put_number(table_name, "centery", -1)
            self.put_number(table_name, "radius", -1)
            self.put_number(table_name, "anglex", -10000)
        else:
            self.put_number(table_name, "centerx", circle.x)
            self.put_number(table_name, "centery", circle.y)
            self.put_number(table_name, "radius", circle.radius)
            self.put_number(table_name, "anglex", circle.anglex)

    def put_ellipse(self, table_name: str, circle: typing.Optional[EllipseDefinition]):
        if circle is None:
            self.put_number(table_name, "centerx", -1)
            self.put_number(table_name, "centery", -1)
            self.put_number(table_name, "d1", -1)
            self.put_number(table_name, "d2", -1)
            self.put_number(table_name, "anglex", -10000)
        else:
            self.put_number(table_name, "centerx", circle.x)
            self.put_number(table_name, "centery", circle.y)
            self.put_number(table_name, "d1", circle.d1)
            self.put_number(table_name, "d2", circle.d2)
            self.put_number(table_name, "anglex", circle.anglex)
