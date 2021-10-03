
import numpy as np

from state import ApplicationState, StateManager
from data import TokenManager
from skimage.metrics import structural_similarity as ssim
from gui import GUIManager
from cg import CVManager
import threading
from data import SyncServer
def background_thread(cv, token):
    while(True):
        cv.get_frame()
        token.update_token(cv.results, cv.last_frame)   

def main():
    gui = GUIManager()
    gui.read_events()
    cv = CVManager()
    server = SyncServer()
    server.start()
    token = TokenManager()
    thread = threading.Thread(target=background_thread, args=(cv,token), daemon=True)
    stateManager = StateManager()
    stateManager.set_state(ApplicationState.DEFINETRANSFORM)
    transMatrix = np.array([])
    while True:
        event, values = gui.read_events()
        if event in ('Exit', None):
            break
        elif event == "reset":
            cv.transform = []
            cv.trans_matrix = None
            stateManager.set_state(ApplicationState.DEFINETRANSFORM)
        if stateManager.state == ApplicationState.DEFINETRANSFORM:
            if event == 'graph':
                if(values[event] not in cv.transform and len(cv.transform)<4):
                    cv.transform.append(values[event])
        
            if(len(cv.transform) == 4):
                stateManager.set_state(ApplicationState.ANALYSE)
        elif stateManager.state == ApplicationState.ANALYSE:
            if event in ("s"):
                cv.screenshot()
            if event == "Mark as player":
                token.set_player(values["graph"])
            if event == "Mark as noise":
                print("event fired!")
                token.blacklist_token(values["graph"])
        if not thread.is_alive():
            thread.start()
        gui.display_gui()
        #token.update_token(cv.results, cv.last_frame)
main()