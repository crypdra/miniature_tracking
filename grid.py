class _Grid:
    _instance = None

    def __init__(self, width, height, offset):
        self.width = width
        self.height = height
        self.offset = offset
        self.max_width = 800
        self.max_height = 450
        self.grid_height = self.max_height / self.height
        self.grid_width = self.max_width / self.width
        self.grid = [[0]*self.width for i in range(self.height)]

    def grid_at_position(self, pos):
        (x,y) = pos
        row = y // self.grid_height
        column = x // self.grid_width
        return (int(column), int(row))

def Grid(width, height, offset):
    if _Grid._instance is None:
        _Grid._instance = _Grid(width, height, offset)
    return _Grid._instance