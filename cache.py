from json import load, dump, JSONDecodeError
from time import time

class Cache:
    """
    data example:
        {
            "title": "Пример имени",
            "image": "https://example.com/picture.jpg",
            "score": "7.25",
            "status": "онгоинг",
            "date": "c 5 декабря 2023 г",
            "type": "ТВ сериал",
            "last_updated": 123456789.0168159, Временной отпечаток последнего обновления информации
            "urls": {
                "610": {  ID перевода
                        1: "//example.com/gfjbkjgrg/" Сохранение в таком формате из-за особенности парсинга с кодика
                    }
            }
        }
    """
    def __init__(self, SAVED_DATA_FILE: str, SAVING_PERIOD: int, CACHE_LIVE_TIME: int):
        self._path = SAVED_DATA_FILE
        try:
            self.data = self.get_data_from_file()
        except JSONDecodeError:
            with open(SAVED_DATA_FILE, 'w') as f:
                dump({}, f)
            self.data = {}
        self.__t = time()
        self.period = SAVING_PERIOD*60 # Перевод в секунды из минут
        self.life_time = CACHE_LIVE_TIME*24*60*60 # Перевод в секунды из дней
        print(f"[CACHE] USING CACHE. SAVE_PERIOD: {self.period} sec. LIFE_TIME: {self.life_time} sec. FILE: {self._path}")
    
    def get_data_from_file(self) -> dict:
        """
        Возвращает данные из файла
        """
        with open(self._path, 'r', encoding='UTF-8') as f:
            return load(f)
    
    def save_data_to_file(self):
        """
        Сохраняет данные в файл
        """
        print(f"[CACHE] Data saved to \"{self._path}\"")
        with open(self._path, 'w') as f:
            dump(self.data, f)

    def get_data_by_id(self, id: str) -> dict:
        """
        Получение информации по id тайтла.
        Если информация не найдена, вернётся None
        """
        if id in self.data.keys():
            return self.data[id]
        else:
            raise KeyError("Id not found")
    
    def get_seria(self, id: str, translation_id: str, seria_num: int) -> str:
        if seria_num in self.data[id]['urls'][translation_id].keys():
            return self.data[id]['urls'][translation_id][seria_num]
        else:
            raise KeyError("Id not found")

    def add_seria(self, id: str, translation_id: str, seria_num: int, url: str):
        """
        Добавляет ссылку на серию в заданном качестве
        """
        if id not in self.data.keys():
            raise KeyError("Id not found")
        else:
            if not self.is_translation(id, translation_id):
                self.add_translation(id, translation_id)
            self.data[id]['urls'][translation_id][seria_num] = url
        
        if time() - self.__t > self.period:
            self.__t = time()
            self.save_data_to_file()
    
    def add_id(self, id: str, title: str, img_url: str, score: str, status: str, dates: str, ttype: str, rating: str):
        data = {
            "title": title,
            "image": img_url,
            "score": score,
            "status": status,
            "date": dates,
            "type": ttype,
            "rating": rating,
            "last_updated": time(),
            "urls": {
            }
        }
        if self.is_id(id):
            del self.data[id]
        self.data[id] = data
        if time() - self.__t > self.period:
            self.__t = time()
            self.save_data_to_file()

    def add_translation(self, id: str, translation_id: str):
        if id in self.data.keys():
            self.data[id]['urls'][translation_id] = {}
        else:
            raise KeyError("Id not found")
        if time() - self.__t > self.period:
            self.__t = time()
            self.save_data_to_file()
    
    def change_image(self, id: str, image_src: str):
        if self.is_id(id):
            temp = self.get_data_by_id(id)
            temp['image'] = image_src
            del self.data[id]
            self.data[id] = temp

    def is_id(self, id: str) -> bool:
        try:
            if id in self.data.keys():
                return True
            else:
                return False 
        except KeyError:
            return False

    def is_translation(self, id: str, translation_id: str) -> bool:
        try:
            if translation_id in self.data[id]['urls'].keys():
                return True
            else:
                return False
        except KeyError:
            return False
        
    def is_seria(self, id: str, translation_id: str, seria_num: int) -> bool:
        try:
            if seria_num in self.data[id]['urls'][translation_id].keys():
                return True
            else:
                return False
        except KeyError:
            return False
