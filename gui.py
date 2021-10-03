
import PySimpleGUI as sg
from cg import CVManager
from state import ApplicationState, StateManager
import cv2

width = 1600
height = 900
QT_ENTER_KEY1 =  'special 16777220'
QT_ENTER_KEY2 =  'special 16777221'
class _GUIManager:
    _instance = None
    def __init__(self):
        right_click_menu = ['', ['Mark as player', 'Mark as noise']]
        self.layout = [[sg.Text("Placeholder", key="info")],[sg.Graph((width,height),(0,height), (width,0), key='graph', enable_events=True, drag_submits=True, right_click_menu=right_click_menu)],[sg.Button('Reset Transform', key="reset")]]
        self.window = sg.Window('The Gate - Digital Miniatures', self.layout, return_keyboard_events=True)
        self.cv = CVManager()
        self.a_id = None
        StateManager().attach(self.change_state)
    def change_state(self, target):
        if target == ApplicationState.DEFINETRANSFORM:
            self.window["info"].update("Please define transform for perspective warping!")
        elif target == ApplicationState.DEFINEOFFSET:
            self.window["info"].update("Please define offset!")
        elif target == ApplicationState.ANALYSE:
            self.window["info"].update("Analyzing image")
    def read_events(self):
        return self.window.read(timeout=100)
    def display_gui(self):
        if self.a_id:
            self.window["graph"].delete_figure(self.a_id)
        if self.cv.last_frame is not None:
            data = cv2.imencode('.ppm', self.cv.last_frame)[1].tobytes() 
            self.a_id = self.window["graph"].draw_image(data=data, location=(0,0))    # draw new image
            self.window["graph"].send_figure_to_back(self.a_id) 



def GUIManager():
    if _GUIManager._instance is None:
        _GUIManager._instance = _GUIManager()
    return _GUIManager._instance
