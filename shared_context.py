import pathlib
import threading
import typing

import numpy

import app_contexts

class LastFrame:
    frame: numpy.ndarray
    timestamp: float
    circle: typing.Optional[numpy.ndarray]

    def __init__(self, frame: numpy.ndarray, timestamp: float, circle: typing.Optional[numpy.ndarray]):
        self.frame = frame
        self.timestamp = timestamp
        self.circle = circle
        self.lock = threading.Lock()

    def get_frame_and_circle(self):
        with self.lock:
            return self.frame, self.circle

    def set_frame_and_circle(self, frame: numpy.ndarray, circle: typing.Optional[numpy.ndarray]):
        with self.lock:
            self.frame = frame
            self.circle = circle


config_file = pathlib.Path("ballfinder.json")
if not config_file.exists():
    app_contexts.save_app_context(config_file, app_contexts.get_default_app_context())
app_context = app_contexts.load_app_context(config_file)
resolution = (320, 240)
last_seen = LastFrame(numpy.zeros((
        resolution[1],
        resolution[0],
    )), 0, None)
