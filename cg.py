
import numpy as np
import cv2
from state import ApplicationState, StateManager
import torch
import time
import enum
import threading 
import os

width = 1600
height = 900
def compute_matrix(pts):
    maxWidth=width
    maxHeight=height
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype = "float32")
    M = cv2.getPerspectiveTransform(pts, dst)   
    return M
def four_point_transform(image, M):
    maxWidth=width
    maxHeight=height
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
    return warped

class _CVManager:
    _instance = None
    def __init__(self):
        self.fresh = FreshestFrame()
        self.transform = []
        self.stateManager = StateManager()
        self.stateManager.attach(self.change_state)
        self.model = torch.hub.load('ultralytics/yolov5', 'custom', path='./model/best_saved.pt')
        self.saved = None
        self.results = []
        self.last_frame = None
        self.saved_frame = None
        self.trans_matrix = None
    def change_state(self, target):
        pass
    def prepare_frame(self, annotate=True):
        ret, frame = self.fresh.read()
        rescale_factor = width/frame.shape[1]
        frame = cv2.resize(frame, (int(frame.shape[1]*rescale_factor),int(frame.shape[0]*rescale_factor)))
        if(self.stateManager.state == ApplicationState.DEFINETRANSFORM):
            for pos in self.transform:
                if annotate:
                    cv2.circle(frame,pos,5,(255,0,0),-1)
        elif(self.stateManager.state == ApplicationState.ANALYSE):
            if(self.trans_matrix is None):
                self.transMatrix = compute_matrix(np.array(self.transform).astype(np.float32))
            frame = four_point_transform(frame, self.transMatrix)
            results = self.model(frame, size=640)
            self.results = []
            
            for result in results.xyxy[0].detach().numpy():
                if(result[4] > 0.6):
                    self.results.append(result)
                    if annotate:
                        cv2.rectangle(frame,(int(result[0]),int(result[1])),(int(result[2]),int(result[3])),(255,0,0),5)
        return frame

    def screenshot(self):
        frame = self.prepare_frame(False)
        ts = str(time.time())
        # subframe !! frame = frame[int(result[1]):int(result[3]), int(result[0]):int(result[2])]
        cv2.imwrite("images/"+ ts + ".jpg", frame)
        print("Saved screenshot to " + ts + ".jpg")

    def get_frame(self):
        frame = self.prepare_frame()
        self.last_frame = frame

        imgbytes=cv2.imencode('.ppm', frame)[1].tobytes()
        return imgbytes


class FrameCallbackHandler:
    class Types(enum.Enum):
        ADDPOSITION = 1
        GRIDBEGIN = 2
        GRIDSELECT = 3

    def __init__(self):
        self.posList = []
        self.gridBegin = (0, 0)
        self.grid = Grid(13, 7, 0)

    def register_callback(self, window, function):
        cv2.namedWindow(window, cv2.WINDOW_AUTOSIZE)
        if function == self.Types.ADDPOSITION:
            cv2.setMouseCallback(window, self.onMouse)
        elif function == self.Types.GRIDBEGIN:
            cv2.setMouseCallback(window, self.onMouseGridBegin)
        elif function == self.Types.GRIDSELECT:
            cv2.setMouseCallback(window, self.onMouseGridSelect)

    def onMouse(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.posList.append((x, y))
            print("Button down!")

    def onMouseGridBegin(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.gridBegin = (x, y)
            print("Begin grid!")

    def onMouseGridSelect(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.grid.set_token_position((x, y))
            print("Select grid!")


class FreshestFrame(threading.Thread):
    def __init__(self, name='FreshestFrame'):
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;udp"
        self.capture = cv2.VideoCapture("rtsp://192.168.178.88")
        #self.capture = cv2.VideoCapture(0)
        #self.capture.set(cv2.CAP_PROP_FPS, 30)
        width = 2048
        height = 1080
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        assert self.capture.isOpened()

        # this lets the read() method block until there's a new frame
        self.cond = threading.Condition()

        # this allows us to stop the thread gracefully
        self.running = False

        # keeping the newest frame around
        self.frame = None

        # passing a sequence number allows read() to NOT block
        # if the currently available one is exactly the one you ask for
        self.latestnum = 0

        # this is just for demo purposes
        self.callback = None

        super().__init__(name=name)
        self.start()

    def start(self):
        self.running = True
        super().start()

    def release(self, timeout=None):
        self.running = False
        self.join(timeout=timeout)
        self.capture.release()

    def run(self):
        counter = 0
        while self.running:
            # block for fresh frame
            (rv, img) = self.capture.read()
            assert rv
            counter += 1

            # publish the frame
            with self.cond:  # lock the condition for this operation
                self.frame = img if rv else None
                self.latestnum = counter
                self.cond.notify_all()

            if self.callback:
                self.callback(img)

    def read(self, wait=True, seqnumber=None, timeout=None):


        with self.cond:
            if wait:
                if seqnumber is None:
                    seqnumber = self.latestnum+1
                if seqnumber < 1:
                    seqnumber = 1

                rv = self.cond.wait_for(
                    lambda: self.latestnum >= seqnumber, timeout=timeout)
                if not rv:
                    return (self.latestnum, self.frame)

            return (self.latestnum, self.frame)


def CVManager():
    if _CVManager._instance is None:
        _CVManager._instance = _CVManager()
    return _CVManager._instance
