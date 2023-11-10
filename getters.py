import requests
import lxml
import json
from bs4 import BeautifulSoup as Soup
from base64 import b64decode
from time import sleep, time
from cache import Cache
import config


def convert_char(char: str):
    low = char.islower()
    alph = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if char.upper() in alph:
        ch = alph[(alph.index(char.upper())+13)%len(alph)]
        if low:
            return ch.lower()
        else:
            return ch
    else:
        return char

def convert(string: str):
    # Декодирование строки со ссылкой
    return "".join(map(convert_char, list(string)))

def get_url_data(url: str, headers: dict = None, session=None):
    return requests.get(url, headers=headers).text

def is_serial(iframe_url: str) -> bool:
    return True if iframe_url[iframe_url.find(".info/")+6] == "s" else False

def is_video(iframe_url: str) -> bool:
    return True if iframe_url[iframe_url.find(".info/")+6] == "v" else False

def generate_translations_dict(series_count: int, translations_div: Soup) -> dict:
    """Returns: {'series_count': series_count, 'translations': translations}"""
    if not isinstance(translations_div, Soup) and translations_div != None:
        translations = []
        for translation in translations_div:
            a = {}
            a['id'] = translation['value']
            a['type'] = translation['data-translation-type']
            if a['type'] == 'voice':
                a['type'] = "Озвучка:  "
            elif a['type'] == 'subtitles':
                a['type'] = "Субтитры: "
            a['name'] = translation.text
            translations.append(a)
    else:
        translations = [{"id": "0", "type": "Неизвестно: ", "name": "Неизвестно"}]

    return {'series_count': series_count, 'translations': translations}

def get_link_to_serial_info(id: str, id_type: str, token: str):
    if id_type == "shikimori":
        serv = f"https://kodikapi.com/get-player?title=Player&hasPlayer=false&url=https%3A%2F%2Fkodikdb.com%2Ffind-player%3FshikimoriID%3D{id}&token={token}&shikimoriID={id}"
    elif id_type == "kinopoisk":
        serv = f"https://kodikapi.com/get-player?title=Player&hasPlayer=false&url=https%3A%2F%2Fkodikdb.com%2Ffind-player%3FkinopoiskID%3D{id}&token={token}&kinopoiskID={id}"
    else:
        raise ValueError("Неизвестный тип id")
    return get_url_data(serv)

def get_serial_info(id: str, id_type: str, token: str) -> dict:
    """Returns dict {'series_count': int, 'translations': [{'id': 'str', 'type': 'str', 'name': 'str'}, ...]}
    If series_count == 0, then it's a video (doesn't have series)
    """
    url = get_link_to_serial_info(id, id_type, token)
    url = json.loads(url)
    is_found = url['found']
    if not is_found:
        raise FileNotFoundError
    else:
        url = url['link']
        url = "https:"+url
        data = get_url_data(url)
        soup = Soup(data, 'lxml')
        if is_serial(url):
            series_count = len(soup.find("div", {"class": "serial-series-box"}).find("select").find_all("option"))
            try:
                translations_div = soup.find("div", {"class": "serial-translations-box"}).find("select").find_all("option")
            except:
                translations_div = None
            return generate_translations_dict(series_count, translations_div)
        elif is_video(url):
            series_count = 0
            try:
                translations_div = soup.find("div", {"class": "movie-translations-box"}).find("select").find_all("option")
            except AttributeError:
                translations_div = None
            return generate_translations_dict(series_count, translations_div)
        else:
            raise FileNotFoundError("NOT A VIDEO NOR A SERIAL!!!")

def get_download_link(id: str, id_type: str, seria_num: int, translation_id: str, token: str):
    if id_type == "shikimori":
        serv = f"https://kodikapi.com/get-player?title=Player&hasPlayer=false&url=https%3A%2F%2Fkodikdb.com%2Ffind-player%3FshikimoriID%3D{id}&token={token}&shikimoriID={id}"
    elif id_type == "kinopoisk":
        serv = f"https://kodikapi.com/get-player?title=Player&hasPlayer=false&url=https%3A%2F%2Fkodikdb.com%2Ffind-player%3FkinopoiskID%3D{id}&token={token}&kinopoiskID={id}"
    else:
        raise ValueError("Неизвестный тип id")
    data = get_url_data(serv)
    url = json.loads(data)['link']
    data = get_url_data('https:'+url)
    soup = Soup(data, 'lxml')
    if translation_id != "0" and seria_num != 0:
        # Обычный сериал (1+ серий)
        container = soup.find('div', {'class': 'serial-translations-box'}).find('select')
        media_hash = None
        media_id = None
        for translation in container.find_all('option'):
            if translation.get_attribute_list('data-id')[0] == translation_id:
                media_hash = translation.get_attribute_list('data-media-hash')[0]
                media_id = translation.get_attribute_list('data-media-id')[0]
                break
        url = f'https://kodik.info/serial/{media_id}/{media_hash}/720p?d=kodik.cc&d_sign=9945930febce35101e96ce0fe360f9729430271c19941e63c5208c2f342e10ed&pd=kodik.info&pd_sign=09ffe86e9e452eec302620225d9848eb722efd800e15bf707195241d9b7e4b2b&ref=&ref_sign=208d2a75f78d8afe7a1c73c2d97fd3ce07534666ab4405369f4f8705a9741144&advert_debug=true&min_age=16&first_url=false&season=1&episode={seria_num}'
        data = get_url_data(url)
        soup = Soup(data, 'lxml')
    
    elif translation_id != "0" and seria_num == 0:
        # Видео с несколькими переводами
        container = soup.find('div', {'class': 'movie-translations-box'}).find('select')
        media_hash = None
        media_id = None
        for translation in container.find_all('option'):
            if translation.get_attribute_list('data-id')[0] == translation_id:
                media_hash = translation.get_attribute_list('data-media-hash')[0]
                media_id = translation.get_attribute_list('data-media-id')[0]
                break
        url = f'https://kodik.info/video/{media_id}/{media_hash}/720p?d=kodik.cc&d_sign=9945930febce35101e96ce0fe360f9729430271c19941e63c5208c2f342e10ed&pd=kodik.info&pd_sign=09ffe86e9e452eec302620225d9848eb722efd800e15bf707195241d9b7e4b2b&ref=&ref_sign=208d2a75f78d8afe7a1c73c2d97fd3ce07534666ab4405369f4f8705a9741144&advert_debug=true&min_age=16&first_url=false&season=1&episode={seria_num}'
        data = get_url_data(url)
        soup = Soup(data, 'lxml')

    
    hash_container = soup.find_all('script')[4].text
    video_type = hash_container[hash_container.find('.type = \'')+9:]
    video_type = video_type[:video_type.find('\'')]
    video_hash = hash_container[hash_container.find('.hash = \'')+9:]
    video_hash = video_hash[:video_hash.find('\'')]
    video_id = hash_container[hash_container.find('.id = \'')+7:]
    video_id = video_id[:video_id.find('\'')]

    download_url = str(get_download_link_with_data(video_type, video_hash, video_id, seria_num)).replace("https://", '')
    download_url = download_url[2:-26] # :hls:manifest.m3u8

    return download_url

def get_download_link_with_data(video_type: str, video_hash: str, video_id: str, seria_num: int):
    params={
        # Данные для теста: hash: "6476310cc6d90aa9304d5d8af3a91279"  id: 19850  type: video
        "hash": video_hash,
        "id": video_id,
        "quality":"720p",
        "type":video_type,
        "protocol": '',
        "host":"kodik.cc",
        "d":"kodik.cc",
        "d_sign":"9945930febce35101e96ce0fe360f9729430271c19941e63c5208c2f342e10ed",
        "pd":"kodik.cc",
        "pd_sign":"9945930febce35101e96ce0fe360f9729430271c19941e63c5208c2f342e10ed",
        "ref": '',
        "ref_sign":"208d2a75f78d8afe7a1c73c2d97fd3ce07534666ab4405369f4f8705a9741144",
        "advert_debug": True,
        "first_url": False,
    }

    data = requests.post('http://kodik.cc/gvi', params=params).json()

    url = convert(data['links']['720'][0]['src'])
    try:
        return b64decode(url.encode())
    except:
        return str(b64decode(url.encode()+b'==')).replace("https:", '')

def get_search_data(search_query: str, token: str, ch: Cache = None):
    payload = {
        "token": token,
        "title": search_query
    }
    url = "https://kodikapi.com/search"
    data = requests.post(url, data=payload).json()
    items = []
    others = []
    used_ids = []
    for item in data['results']:
        if 'shikimori_id' in item.keys() and item['shikimori_id'] not in used_ids:
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
                'image': ser_data['image'],
                'id': item['shikimori_id'],
                'type': ser_data['type'],
                'date': ser_data['date'],
                'title': item['title'],
                'status': ser_data['status']
            }
            items.append(dd)
            used_ids.append(item['shikimori_id'])
        elif "kinopoisk_id" in item.keys() and 'shikimori_id' not in item.keys() and item['kinopoisk_id'] not in used_ids:
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

def get_shiki_data(id: str, retries: int = 3, alph: str = 'zzyxwvutsrqponmlkjihgfedcba'):
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 OPR/93.0.0.0 (Edition Yx GX)",
    }
    if retries <= 0:
        print(f"Max retries getting data exceeded. Id: {id}")
        raise RuntimeWarning(f"Max retries getting data exceeded. Id: {id}")
    url = "https://shikimori.one/animes/"+id
    data = get_url_data(url, headers)
    if data[data.find('<title>')+7:data.find('</title>')] == '502':
        for i, ch in enumerate(alph):
            if i+1 == len(alph):
                raise RuntimeWarning("Can't generate url")
            if url[url.rfind('/')+1] == ch:
                url = url[:url.rfind('/')+1]+alph[i+1]+url[url.rfind('/')+2:]
            else:
                url = url[:url.rfind('/')+1]+alph[i+1]+url[url.rfind('/')+1:]
            data = get_url_data(url, headers)
            if data[data.find('<title>')+7:data.find('</title>')] != '502':
                break
    soup = Soup(data, 'lxml')
    try:
        if soup.find('img', {'class': 'image'}).get_attribute_list('src')[0] == "/images/static/page_moved.jpg":
            # Проверка на перемещение страницы
            new_id = soup.find("a").get_attribute_list('href')[0]
            new_id = new_id[new_id.rfind('/'):]
            return get_shiki_data(new_id, retries=retries-1)
        else:
            # Страница не перемещена
            raise FileExistsError
    except:
        try:
            if soup.find("div", {'class': 'b-age_restricted'}) == None:
                # Проверка на возрастные ограничения
                soup.find("div", {'class': 'c-poster'}).find('picture').find('img')
            else:
                raise PermissionError
        except PermissionError:
            title = f"18+ (Shikimori id: {id})"
            image = config.IMAGE_AGE_RESTRICTED
            p_data = "Неизвестно"
            dtype = "Неизвестно"
            dstatus = "Неизвестно"
            ddate = "Неизвестно"
            score = "Неизвестно"
        except:
            # Сервер не допукает слишком частое обращение
            sleep(0.5)
            return get_shiki_data(id, retries=retries-1)
        else:
            title = soup.find('header', {'class': 'head'}).find('h1').text
            try:
                image = soup.find("div", {'class': 'c-poster'}).find('div').get_attribute_list('data-href')[0]
            except:
                try:
                    image = soup.find("div", {'class': 'c-poster'}).find('picture').find('img').get_attribute_list('src')[0]
                except:
                    image = config.IMAGE_NOT_FOUND
            p_data = soup.find('div', {'class': 'b-entry-info'}).find_all('div', {'class': 'line-container'})
            dtype = p_data[0].find('div', {'class': 'value'}).text
            dstatus = soup.find('div', {'class': 'b-entry-info'}).find('span', {'class': 'b-anime_status_tag'}).get_attribute_list('data-text')[0]
            ddate = soup.find('div', {'class': 'b-entry-info'}).find('span', {'class': 'b-anime_status_tag'}).parent.text[2:].strip()
            score = soup.find('div', {'class': 'text-score'}).find('div').text
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

if __name__ == "__main__":
    from pprint import pprint
    pprint(get_shiki_data("z20"))