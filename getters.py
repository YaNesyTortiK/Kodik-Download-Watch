from anime_parsers_ru import KodikParser, ShikimoriParser, errors
import requests
from time import sleep, time
from cache import Cache
import config

if config.USE_LXML:
    import lxml

kodik_parser = KodikParser(use_lxml=config.USE_LXML)
shiki_parser = ShikimoriParser(use_lxml=config.USE_LXML)

def get_url_data(url: str, headers: dict = None, session=None):
    return requests.get(url, headers=headers).text

def get_serial_info(id: str, id_type: str, token: str) -> dict:
    return kodik_parser.get_info(id, id_type)

def get_download_link(id: str, id_type: str, seria_num: int, translation_id: str, token: str):
    return kodik_parser.get_link(id, id_type, seria_num, translation_id)[0]

def get_search_data(search_query: str, token: str, ch: Cache = None):
    search_res = kodik_parser.search(search_query, limit=50)
    items = []
    others = []
    used_ids = []
    for item in search_res:
        if 'shikimori_id' in item.keys() and item['shikimori_id'] != None and item['shikimori_id'] not in used_ids:
            # Проверка на наличие shikimori_id и на отсутствие его в уже добавленных тайтлах
            if ch != None and ch.is_id("sh"+item['shikimori_id']):
                # Проверка на наличие данных в кеше
                ch_ser_data = ch.get_data_by_id("sh"+item['shikimori_id'])
                if time() - ch_ser_data['last_updated'] > ch.life_time:
                    # Обновление данных если они устарели (CACHE_LIFE_TIME был превышен)
                    try:
                        ser_data = get_shiki_data(item['shikimori_id'])
                    except RuntimeWarning:
                        continue
                    ch.add_id("sh"+item['shikimori_id'],
                        ser_data['title'], ser_data['image'], ser_data['score'], ser_data['status'], ser_data['date'], ser_data['type'])
                else:
                    ser_data = ch_ser_data
            else:
                # Если данных в кеше нет или кеш не используется
                try:
                    ser_data = get_shiki_data(item['shikimori_id'])
                except RuntimeWarning:
                    continue
                if ch != None:
                    ch.add_id("sh"+item['shikimori_id'],
                        ser_data['title'], ser_data['image'], ser_data['score'], ser_data['status'], ser_data['date'], ser_data['type'])
            dd = {
                'image': ser_data['image'] if ser_data['image'] != None else config.IMAGE_NOT_FOUND,
                'id': item['shikimori_id'],
                'type': ser_data['type'],
                'date': ser_data['date'],
                'title': item['title'],
                'status': ser_data['status']
            }
            items.append(dd)
            used_ids.append(item['shikimori_id'])
        elif "kinopoisk_id" in item.keys() and item['kinopoisk_id'] != None and ('shikimori_id' not in item.keys() or item['shikimori_id'] is None) and item['kinopoisk_id'] not in used_ids:
            if item['type'] == "foreign-movie":
                ctype = "Иностранный фильм"
            elif item['type'] == "foreign-serial":
                ctype = "Иностранный сериал"
            elif item['type'] == "russian-movie":
                ctype = "Русский фильм"
            elif item['type'] == "russian-serial":
                ctype = "Русский сериал"
            else:
                ctype = item['type']
            others.append(
                {
                    "id": item['kinopoisk_id'],
                    "title": item['title'],
                    "type": ctype,
                    "date": item['year']
                }
            )
            used_ids.append(item['kinopoisk_id'])

    others = sorted(others, key=lambda x: x['date'], reverse=True)
    return (items, others)

def get_shiki_data(id: str, retries: int = 3):
    if retries <= 0:
        print(f"Max retries getting data exceeded. Id: {id}")
        raise RuntimeWarning(f"Max retries getting data exceeded. Id: {id}")
    try:
        data = shiki_parser.anime_info(shiki_parser.link_by_id(id))
    except errors.AgeRestricted:
        title = f"18+ (Shikimori id: {id})"
        image = config.IMAGE_AGE_RESTRICTED
        dtype = "Неизвестно"
        dstatus = "Неизвестно"
        ddate = "Неизвестно"
        score = "Неизвестно"
    except errors.TooManyRequests:
        # Сервер не допукает слишком частое обращение
        sleep(0.5)
        return get_shiki_data(id, retries=retries-1)
    except errors.NoResults:
        raise RuntimeWarning
    else:
        title = data['title']
        image = data['picture']
        dtype = data['type']
        ddate = data['dates']
        dstatus = data['status']
        score = data['score']
    return {
        'title': title,
        'image': image,
        'type': dtype,
        'date': ddate,
        'status': dstatus,
        'score': score
    }
    
def is_good_quality_image(src: str) -> bool:
    if "preview" in src or "main_alt" in src:
        return False
    else:
        return True
