# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
from threading import Thread, Semaphore
import cv2
import time
mutex=Semaphore(1)
import threading


class PiVideoStream:
	def __init__(self, resolution=(320, 240), framerate=30):
		# initialize the camera and stream
		self.camera = PiCamera()
		self.camera.resolution = resolution
		self.camera.framerate = framerate
		self.rawCapture = PiRGBArray(self.camera, size=resolution)
		self.stream = self.camera.capture_continuous(self.rawCapture,
			format="bgr", use_video_port=True)
		# initialize the frame and the variable used to indicate
		# if the thread should be stopped
		self.frame = None
		self.parsedFrame=None
		self.stopped = False
		self.frameTime=time.time()
		self.cv = threading.Condition()
		self.newFrame=False
		self.filterCallback = None
		#self.staticFrame = cv2.imread("./Picture1.bmp")

	def getResolution(self):
		return self.camera.resolution

	def setImageFilter(self, filterCallback):
		self.filterCallback = filterCallback

	def start(self):
		# start the thread to read frames from the video stream
		Thread(target=self.update, args=()).start()
		return self

	def update(self):
		# keep looping infinitely until the thread is stopped
		total_frames_read = 0
		start_time = time.time()
		for f in self.stream:
			# grab the frame from the stream and clear the stream in
			# preparation for the next frame
			#mutex.acquire()
			with self.cv:
				self.frame = f.array
				self.frameTime=time.time()
				if self.filterCallback is not None:

					self.parsedFrame = self.filterCallback(self.frame)
					total_frames_read += 1
					if time.time() - start_time > 10:
						print(f"read: {total_frames_read}")
						start_time = time.time()
						total_frames_read = 0

				self.newFrame=True
				self.cv.notify_all()
			#mutex.release()
			self.rawCapture.truncate(0)
			# if the thread indicator variable is set, stop the thread
			# and resource camera resources
			if self.stopped:
				self.stream.close()
				self.rawCapture.close()
				self.camera.close()
				return

	def read(self):
		# return the frame most recently read
		#mutex.acquire()
		with self.cv:
			while not self.newFrame:
				self.cv.wait()
			newFrame=False
			if self.parsedFrame is not None:
				temp = (self.parsedFrame, self.frameTime)
			else:
				temp = (self.frame, self.frameTime)
		#mutex.release()
		return temp #self.staticFrame #temp

	def readAny(self):
		return self.frame

	def stop(self):
		# indicate that the thread should be stopped
		self.stopped = True
