from time import time
from hashlib import md5

class Manager:
    def __init__(self, remove_time: int):
        # remove_time - minutes через какое время простоя комната будет удалена
        self.rooms = {}
        self.remove_time = remove_time * 60

    def new_room(self, data: dict) -> str:
        now = time()
        hsh = md5(str(now).encode('utf-8')).hexdigest()
        self.rooms[hsh] = data
        self.rooms[hsh]['last_used'] = now
        return hsh
    
    def is_room(self, id: str) -> bool:
        if id in self.rooms.keys():
            return True
        else:
            return False
    
    def get_room_data(self, id: str) -> dict:
        return self.rooms[id]

    def update_room(self, id: str, data: dict):
        self.rooms[id] = data
        self.room_used(id)

    def update_play_time(self, id: str, play_time: float):
        self.rooms[id]['play_time'] = play_time

    def room_used(self, id: str):
        self.rooms[id]['last_used'] = time()
    
    def remove_old_rooms(self):
        now = time()
        for room_id in self.rooms.keys():
            if self.rooms[room_id]['last_used']+self.remove_time < now:
                del self.rooms[room_id]