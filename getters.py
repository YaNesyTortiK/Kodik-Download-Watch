from anime_parsers_ru import KodikParser, ShikimoriParser, errors, ShikimoriParserAsync
import requests
from time import sleep, time
from cache import Cache
import config
import re
import logging

logging.basicConfig(level=logging.DEBUG)

if config.USE_LXML:
    import lxml

USE_KODIK_SEARCH = False

if not config.KODIK_TOKEN:
    try:
        # Проверяем, может ли токен получить доступ к апи полностью
        kodik_parser = KodikParser(use_lxml=config.USE_LXML, validate_token=True)
    except errors.TokenError:
        print("Токен неверен для нескольких функций. Поиск будет происходить по шикимори.")
        # Если не может, то без валидации (поиск будет через шики)
        kodik_parser = KodikParser(use_lxml=config.USE_LXML, validate_token=False)
    else:
        # Если ошибки по токену нет, значит используем поиск по кодику
        USE_KODIK_SEARCH = True
else:
    # Токен указан в конфиге, поэтому принимается за полностью рабочий
    # и проходит полную валидацию
    kodik_parser = KodikParser(token=config.KODIK_TOKEN, use_lxml=config.USE_LXML, validate_token=True)
    USE_KODIK_SEARCH = True

shiki_parser = ShikimoriParser(use_lxml=config.USE_LXML)


def get_seria_link(shikimori_id: str, seria_num: int, translation_id: str):
    print(type(shikimori_id), shikimori_id)
    print(type(seria_num), seria_num)
    print(type(translation_id), translation_id)
    
    return kodik_parser.get_m3u8_playlist_link(
        id=shikimori_id,
        id_type="shikimori",
        seria_num=seria_num,
        translation_id=translation_id,
        quality=720)

def get_url_data(url: str, headers: dict = None, session=None):
    return requests.get(url, headers=headers).text

# 'translations': [
# {
# 'id': id перевода/субтитров/озвучки
# 'type': тип (voice/subtitles)
# 'name': Имя автора озвучки/субтитров
# },
priority_order = [
    "Дублированный",
    "ТО Дубляжная",
    "Studio Band",
    "AniLiberty (AniLibria)",
    "AniLibria.TV",
    "JAM",
    "Dream Cast",
    "SHIZA Project",
    "Reanimedia",
    "AnimeVost"
]

# создаём словарь для быстрого поиска индекса приоритета
priority_index = {name: i for i, name in enumerate(priority_order)}


def sort_key(item):
    name = item.get("name", "")
    series_count = item.get("series_count", 0)
    for p_name in priority_order:
        if name.startswith(p_name):
            priority = priority_index[p_name]
            break
    else:
        priority = float('inf')
    return (-series_count, priority, name)

def format_translations(translations):
    priority_list = []
    normal_list = []
    subs = []
    for t in translations:
        if t.get("type") != "Озвучка":
            subs.append(t)
            continue
        name = t.get("name", "")
        match = re.search(r'\((\d+)', t["name"])
        t["series_count"] = int(match.group(1)) if match else 0
        if any(name.startswith(p) for p in priority_order):
            priority_list.append(t)
        else:
            normal_list.append(t)

    priority_list.sort(key=sort_key)
    normal_list.sort(key=sort_key)
    subs.sort(key=sort_key)
    return priority_list, normal_list, subs
# пример использования

def get_serial_info(id: str, id_type: str, token: str) -> dict:
    data = kodik_parser.get_info(id, id_type)
    temp = data


    try:
        priority_list, normal_list, subs = format_translations(data["translations"])
        data["translations"] = priority_list + normal_list + subs
        data["top_translations"] = priority_list
        data["etc_translations"] = normal_list + subs

    except:
        temp["top_translations"] = data
        temp["etc_translations"] = []

        return temp
    return data

def get_download_link(id: str, id_type: str, seria_num: int, translation_id: str, token: str):
    return kodik_parser.get_link(id, id_type, seria_num, translation_id)[0]

def get_search_data(search_query: str, token: str | None, ch: Cache = None):
    if USE_KODIK_SEARCH:
        search_res = kodik_parser.search(search_query, limit=50)
    else:
        search_res = shiki_parser.search(search_query)
        # Если хотите использовать GraphQL для поиска, то закомментируйте строку выше, и раскомментируйте эту
        # search_res = [{"shikimori_id": x['id'], 'title': x['russian']} for x in shiki_parser.deep_search(search_query, return_parameters=['id', 'russian'])]

    items = []
    others = []
    used_ids = []
    for item in search_res:
        # Проверка на наличие shikimori_id и на отсутствие его в уже добавленных тайтлах
        if 'shikimori_id' in item.keys() and item['shikimori_id'] != None and item['shikimori_id'] not in used_ids:
            if ch != None and ch.is_id("sh"+item['shikimori_id']): # Проверка на наличие данных в кеше
                ser_data = ch.get_data_by_id("sh"+item['shikimori_id'])
            else: # Если данных в кеше нет или кеш не используется
                try:
                    ser_data = get_shiki_data(item['shikimori_id'])
                except RuntimeWarning:
                    continue
                if ch != None:
                    ch.add_id("sh"+item['shikimori_id'],
                        ser_data['title'], ser_data['image'], ser_data['score'], ser_data['status'], ser_data['date'], ser_data['year'], ser_data['type'], ser_data['rating'], ser_data['description'])
            dd = {
                'image': ser_data['image'] if ser_data['image'] != None else config.IMAGE_NOT_FOUND,
                'id': item['shikimori_id'],
                'type': ser_data['type'],
                'date': ser_data['date'],
                'title': item['title'],
                'status': ser_data['status'],
                'year': ser_data['year'],
                'description': ser_data['description']
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
        if config.ALLOW_NSFW:
            try:
                d = shiki_parser.deep_anime_info(id, [
                    'russian', 'kind', 'rating', 'status', 'releasedOn { year, date }', 'score', 'poster { originalUrl }', 'description'
                ])
                title = d['russian']
                image = d['poster']['originalUrl']
                dtype = d['kind']
                dstatus = d['status']
                dyear = d['releasedOn']['year'] if d['releasedOn']['year'] else 1970
                ddate = d['releasedOn']['date']
                score = d['score']
                rating = d['rating']
                description = d['description']
            except:
                title = f"18+ (Shikimori id: {id})"
                image = config.IMAGE_AGE_RESTRICTED
                dtype = "Неизвестно"
                dstatus = "Неизвестно"
                ddate = "Неизвестно"
                score = "Неизвестно"
                rating = '18+'
                dyear = 1970
                description = 'Неизвестно'
        else:
            title = f"18+ (Shikimori id: {id})"
            image = config.IMAGE_AGE_RESTRICTED
            dtype = "Неизвестно"
            dstatus = "Неизвестно"
            ddate = "Неизвестно"
            score = "Неизвестно"
            rating = '18+'
            dyear = 1970
            description = 'Неизвестно'
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
        rating = data['rating']
        description = data['description']
        dyear = data['dates'][-7:-3] if not(data['dates'] is None) and data['dates'][-7:-3].isdigit() else 1970
    return {
        'title': title,
        'image': image,
        'type': dtype,
        'date': ddate,
        'status': dstatus,
        'score': score,
        'rating': rating,
        'description': description,
        'year': dyear
    }

def get_related(id: str, id_type: str, sequel_first: bool = False) -> list:
    # Поддерживается только shikimori id. Поиск связанных аниме
    id_type = 'shikimori' if id_type == 'sh' else id_type
    if id_type != 'shikimori':
        raise ValueError('Функция поддерживает только shikimori id')
    try:
        link = shiki_parser.link_by_id(id)
    except errors.NoResults:
        raise FileNotFoundError(f'Данные по id {id} не найдены')
    data = shiki_parser.additional_anime_info(link)['related']
    res = []
    for x in data:
        if x['date'] is None:
            x['date'] = 'Неизвестно'
        if x['type'] in ['Манга', 'Ранобэ']:
            x['internal_link'] = x['url']
        else:
            sid = shiki_parser.id_by_link(x['url'])
            x['internal_link'] = f'/download/sh/{sid}/'
        res.append(x)
    if sequel_first:
        return sorted(res, key=lambda x: 0 if x["relation"] == 'Продолжение' else 1)
    else:
        return res

def is_good_quality_image(src: str) -> bool:
    if "preview" in src:
        return False
    else:
        return True
