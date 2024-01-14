import collections
import contextlib
import threading
import time
import typing

import numpy
from picamera.array import PiRGBArray
from picamera import PiCamera

import logger


# @contextlib.contextmanager
# def get_camera(resolution=(320, 240), framerate=60):
#     # Yields a camera object

#     try:
#         # Initialize the camera and grab a reference to the raw camera capture
#         camera = PiCamera()
#         camera.resolution = resolution
#         camera.framerate = framerate

#         # Allow the camera to warmup
#         time.sleep(0.1)

#         yield camera

#     finally:
#         # Close the camera
#         print("Closing camera")
#         camera.close()


# @contextlib.contextmanager
# def get_raw_capture(camera, resolution=(320, 240)):
#     # Yields a raw capture object

#     try:
#         raw_capture = PiRGBArray(camera, size=resolution)

#         yield raw_capture

#     finally:
#         print("Closing raw capture")
#         raw_capture.close()


class TimedFrame(typing.NamedTuple):
    frame: numpy.ndarray
    time: float


def get_images(resolution=(320, 240), framerate=30):
    """
    Gets images from the picamera

    :param resolution: The resolution of the images
    :param framerate: The framerate of the images

    :return: The images
    """

    image_lock = threading.Lock()

    # Initialize the camera and grab a reference to the raw camera capture
    with contextlib.closing(PiCamera()) as camera:
        camera.resolution = resolution
        camera.framerate = 30

        with contextlib.closing(PiRGBArray(camera, size=resolution)) as raw_capture:
            # Capture frames from the camera
            try:
                for frame in camera.capture_continuous(raw_capture, format="bgr", use_video_port=True): # type: ignore
                    with image_lock:
                        timestamp = time.time()
                        frame: PiRGBArray
                        # Grab the raw NumPy array representing the image
                        image = frame.array

                        # Clear the stream in preparation for the next frame
                        raw_capture.truncate(0)

                        # Yield the image
                        yield TimedFrame(image, timestamp)
            except:
                logger.exception("Failed to read image")


def transform_images(images: typing.Iterable[TimedFrame], transform: typing.Optional[typing.Callable[[numpy.ndarray], numpy.ndarray]]=None):
    """
    Transforms images from the picamera

    :param images: The images to transform
    :param transform: The function to transform the images with

    :return: The transformed images
    """

    read_count = 0
    start_time = time.time()

    for image in images:
        transformed_frame = transform(image.frame) if transform is not None else image.frame

        yield TimedFrame(
            transformed_frame,
            image.time
        )


if __name__ == "__main__":
    for image in get_images():
        print(image)
        break
