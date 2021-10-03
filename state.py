import enum

class ApplicationState(enum.Enum):
    DEFINETRANSFORM = 1
    DEFINEOFFSET = 2
    DEFINEPCS = 3
    ANALYSE = 4
class _StateManager:
    _instance = None
    def __init__(self):
        self.state = ApplicationState.DEFINETRANSFORM
        self.observers = []
    def attach(self, function):
        self.observers.append(function)
    def set_state(self, state):
        self.state = state
        for f in self.observers:
            f(state)

def StateManager():
    if _StateManager._instance is None:
        _StateManager._instance = _StateManager()
    return _StateManager._instance