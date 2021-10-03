
from grid import Grid
from skimage.metrics import structural_similarity as ssim
import cv2
import threading
import asyncio
import websockets
import json
import threading
class Token:
    def __init__(self, pos, image):
        _instance = None
        self.pos = pos
        self.image = image
        self.last_seen = 0
        self.frame_count = 1
        self.player_token = False
class _SyncServer:
    _instance = None
    def __init__(self):
        self.movement_queue = []
    def start(self):
        loop = asyncio.get_event_loop()
        start_server = websockets.serve(self.movements, 'localhost', 8765)
        t = threading.Thread(target=self.start_loop, args=(loop, start_server))
        t.start()
    def start_loop(self,loop, server):
        loop.run_until_complete(server)
        loop.run_forever()
    async def movements(self, websocket, path):
        while(True):
            try:
                if len(self.movement_queue)>0:
                    message = self.movement_queue.pop(0)  
                else:
                    await asyncio.sleep(0.5)
                    message = {"status": "done"}

                await websocket.send(json.dumps(message))
            except:
                pass

def SyncServer():
    if _SyncServer._instance is None:
        _SyncServer._instance = _SyncServer()
    return _SyncServer._instance

class _TokenManager:
    _instance = None
    def __init__(self):
        self.grid = Grid(12,7,0)
        self.current_token = []
        self.known_token = []
        self.blacklist = []
        self.mutex = threading.Lock()
        self.server = SyncServer()
    def update_token(self, detected, frame):
        self.mutex.acquire()
        token_list = []
        for token in detected:
            pos = self.grid.grid_at_position((int(token[0]+(token[2]-token[0])/2), int(token[1]+(token[3]-token[1])/2)))
            token_list.append(Token(pos, frame[int(token[1])-15:int(token[3]+15), int(token[0])-15:int(token[2])+15]))
        to_pop = []
        for past_token in self.current_token:
            past_token.last_seen += 1
        for known in self.known_token:
            known.last_seen += 1
        for key, token in reversed(list(enumerate(token_list[:]))):
            for past_token in self.current_token[:]:
                if(token.pos == past_token.pos):
                    past_token.last_seen = 0
                    past_token.frame_count += 1
                    token_list.pop(key)
                    break


        for tokenkey, token in reversed(list(enumerate(token_list[:]))):
            # Compare image to known token list
            for knownkey, known in reversed(list(enumerate(self.known_token[:]))):
                if(known.pos == token.pos):
                    print(token.image.shape)
                    print(known.image.shape)
                    try:
                        resized = cv2.resize(token.image, (known.image.shape[1], known.image.shape[0]))
                        score = ssim(known.image, resized, multichannel=True)
                        if score > 0.7:
                            token.frame_count = known.frame_count + 1
                            token.player_token = known.player_token
                            token_list.pop(tokenkey)
                            self.known_token.pop(knownkey)
                            self.current_token.append(token)
                            print("Rediscovered token at: " + str(token.pos))
                            break
                    except:
                        pass

            # Check if token has gone missing in the last x steps
        for tokenkey, token in reversed(list(enumerate(token_list[:]))):
            # Compare image to known token list
            for knownkey, known in reversed(list(enumerate(self.known_token[:]))):
                if known.last_seen < 100:
                    token.frame_count = known.frame_count + 1
                    token.player_token = known.player_token
                    token_list.pop(tokenkey)
                    self.known_token.pop(knownkey)
                    self.current_token.append(token)
                    if(token.pos != known.pos):
                        self.server.movement_queue.append({
                            "moveFrom": {
                                "x": known.pos[0],
                                "y": known.pos[1]
                            }, 
                            "moveTo": {
                                "x": token.pos[0],
                                "y": token.pos[1]
                            }
                        })
                        if token.player_token:
                            print("Player token moved from: " + str(known.pos) +  " to: " + str(token.pos))
                        else: 
                            print("Token moved from: " + str(known.pos) +  " to: " + str(token.pos))
                    break

        for tokenkey, token in enumerate(token_list):
            # Add new token
            blacklist = False
            for blacklisted in self.blacklist:
                resized = cv2.resize(token.image, (blacklisted.image.shape[1], blacklisted.image.shape[0]))
                score = ssim(blacklisted.image, resized, multichannel=True)
                if score > 0.7:
                    blacklist = True
                    break
            if not blacklist:
                print("New token at: " + str(token.pos))
                self.current_token.append(token)


        to_pop = []
        for key, past_token in enumerate(self.current_token):
            if(past_token.last_seen > 0):
                to_pop.append(key)
                self.known_token.append(past_token)
        for x in sorted(to_pop, reverse=True):
            self.current_token.pop(x)
        self.mutex.release()
    def blacklist_token(self, pos):
        print("Waiting for lock!")
        self.mutex.acquire()
        print("Trying to blacklist!")
        gridpos = self.grid.grid_at_position(pos)
        for token in self.current_token:
            if token.pos == gridpos:
                print("Blacklisted: " + str(gridpos))
                self.current_token.remove(token)
                self.blacklist.append(token)
                break
        for token in self.known_token:
            if token.pos == gridpos and token.last_seen < 30:
                print("Blacklisted: " + str(gridpos))
                self.known_token.remove(token)
                self.blacklist.append(token)
                break            
        self.mutex.release()
    def set_player(self, pos):
        self.mutex.acquire()
        gridpos = self.grid.grid_at_position(pos)
        for token in self.current_token:
            if token.pos == gridpos:
                token.player_token = True
        self.mutex.release()
def TokenManager():
    if _TokenManager._instance is None:
        _TokenManager._instance = _TokenManager()
    return _TokenManager._instance