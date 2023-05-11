import requests
import lxml
import json
from bs4 import BeautifulSoup as Soup
from base64 import b64decode
from time import sleep

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
    return "".join(map(convert_char, list(string)))

def get_url_data(url: str, headers: dict = None):
    return requests.get(url, headers=headers).text

def get_shiki_picture(shikimoriID: str):
    """Returns main picture src and score of serial"""
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 OPR/93.0.0.0 (Edition Yx GX)",
    }
    url = f"https://shikimori.one/animes/{shikimoriID}"
    data = get_url_data(url, headers)
    soup = Soup(data, 'lxml')
    if soup.find("p", {"class": "error-404"}) != None:
        url = soup.find("a")['href']
        data = get_url_data(url, headers)
        soup = Soup(data, 'lxml')
    try:
        name = soup.find('header', {'class': 'head'}).find('h1').text
        try:
            picture = soup.find('div', {"class": 'c-poster'}).find("div")['data-href']
        except:
            picture = soup.find('div', {"class": 'c-poster'}).find("img")['src']
        score = soup.find('div', {'class': 'text-score'}).find('div').text
    except:
        raise FileNotFoundError("Ошибка поиска по шики")
    return {"name": name, "pic": picture, "score": score}

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

def get_link_to_serial_info(shikimoriID: str):
    token="447d179e875efe44217f20d1ee2146be"
    serv = f"https://kodikapi.com/get-player?title=Player&hasPlayer=false&url=https%3A%2F%2Fkodikdb.com%2Ffind-player%3FshikimoriID%3D{shikimoriID}&token={token}&shikimoriID={shikimoriID}"
    data = get_url_data(serv)
    return data

def get_shiki_serial_info(shikimoriID: str) -> dict:
    """Returns dict {'series_count': int, 'translations': [{'id': 'str', 'type': 'str', 'name': 'str'}, ...]}
    If series_count == 0, then it's a video (doesn't have series)
    """
    url = get_link_to_serial_info(shikimoriID)
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
            print(translations_div)
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

def get_download_link(shikimori_id: str, seria_num: int, translation_id: str):
    print(shikimori_id, seria_num, translation_id)
    token="447d179e875efe44217f20d1ee2146be"
    serv = f"https://kodikapi.com/get-player?title=Player&hasPlayer=false&url=https%3A%2F%2Fkodikdb.com%2Ffind-player%3FshikimoriID%3D{shikimori_id}&token={token}&shikimoriID={shikimori_id}"
    data = get_url_data(serv)
    url = json.loads(data)['link']
    data = get_url_data('https:'+url)
    soup = Soup(data, 'lxml')
    if translation_id != "0" and seria_num != 0:
        container = soup.find('div', {'class': 'serial-translations-box'}).find('select')
        media_hash = None
        media_id = None
        for translation in container.find_all('option'):
            # print(translation.get_attribute_list('data-id'))
            if translation.get_attribute_list('data-id')[0] == translation_id:
                media_hash = translation.get_attribute_list('data-media-hash')[0]
                media_id = translation.get_attribute_list('data-media-id')[0]
                break
        url = f'https://kodik.info/serial/{media_id}/{media_hash}/720p?d=kodik.cc&d_sign=9945930febce35101e96ce0fe360f9729430271c19941e63c5208c2f342e10ed&pd=kodik.info&pd_sign=09ffe86e9e452eec302620225d9848eb722efd800e15bf707195241d9b7e4b2b&ref=&ref_sign=208d2a75f78d8afe7a1c73c2d97fd3ce07534666ab4405369f4f8705a9741144&advert_debug=true&min_age=16&first_url=false&season=1&episode={seria_num}'
        data = get_url_data(url)
        soup = Soup(data, 'lxml')
    
    elif translation_id != "0" and seria_num == 0:
        container = soup.find('div', {'class': 'movie-translations-box'}).find('select')
        media_hash = None
        media_id = None
        for translation in container.find_all('option'):
            # print(translation.get_attribute_list('data-id'))
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

    download_url = str(get_download_link_with_data(video_type, video_hash, video_id, seria_num))
    download_url = download_url[2:-26] # :hls:manifest.m3u8

    return download_url

def get_download_link_with_data(video_type: str, video_hash: str, video_id: str, seria_num: int):
    params={
        "hash": video_hash, # "6476310cc6d90aa9304d5d8af3a91279"
        "id": video_id, # 19850
        "quality":"720p",
        "type":video_type, # video
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
    if seria_num == 0:
        return str(b64decode(url.encode()+b'==')).replace("https:", '')
    else:
        return b64decode(url.encode())

def get_search_data(search_query: str):
    token="447d179e875efe44217f20d1ee2146be"
    payload = {
        "token": token,
        "title": search_query
    }
    url = "https://kodikapi.com/search"
    data = requests.post(url, data=payload).json()
    items = []
    used_ids = []
    # with open('datta.json', 'w') as f:
    #     json.dump(data['results'], f)
    for item in data['results']:
        # item['type'] == 'anime-serial' and 
        if 'shikimori_id' in item.keys() and item['shikimori_id'] not in used_ids:
            ser_data = get_shiki_data(item['shikimori_id'])
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

    return items

def get_shiki_data(id: str):
    print(id)
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 OPR/93.0.0.0 (Edition Yx GX)",
    }
    url = "https://shikimori.me/animes/"+id
    data = get_url_data(url, headers)
    soup = Soup(data, 'lxml')
    try:
        if soup.find('img', {'class': 'image'}).get_attribute_list('src')[0] == "/images/static/page_moved.jpg":
            new_id = soup.find("a").get_attribute_list('href')[0]
            new_id = new_id[new_id.rfind('/'):]
            return get_shiki_data(new_id)
        else:
            raise FileExistsError
    except:
        try:
            a = soup.find("div", {'class': 'c-poster'}).find('picture').find('img')
        except:
            # Сервер не допукает слишком частое обащение
            sleep(0.5)
            return get_shiki_data(id)
        image = soup.find("div", {'class': 'c-poster'}).find('picture').find('img').get_attribute_list('src')[0]
        p_data = soup.find('div', {'class': 'b-entry-info'}).find_all('div', {'class': 'line-container'})
        dtype = p_data[0].find('div', {'class': 'value'}).text
        dstatus = soup.find('div', {'class': 'b-entry-info'}).find('span', {'class': 'b-anime_status_tag'}).get_attribute_list('data-text')[0]
        ddate = soup.find('div', {'class': 'b-entry-info'}).find('span', {'class': 'b-anime_status_tag'}).parent.text
        return {
            'image': image,
            'type': dtype,
            'date': ddate,
            'status': dstatus
        }


def get_shiki_search_data(search_query: str):
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 OPR/93.0.0.0 (Edition Yx GX)",
    }
    url = f"https://shikimori.me/animes?search={search_query}"
    data = get_url_data(url, headers)
    soup = Soup(data, 'lxml')
    items = []
    for item in soup.find('div', {'class': 'cc-entries'}).find_all('article'):
        dd = {
            'image': item.find('meta').get_attribute_list("content")[0],
            'id': item.get_attribute_list("id")[0],
            'type': item.find('span', {'class': 'misc'}).find_all('span')[1].text,
            'date': item.find('span', {'class': 'misc'}).find_all('span')[0].text,
            'title': item.text,
        }
        dd['title'] = dd['title'].replace(dd['type'], '', 1).replace(dd['date'], '', 1)
        items.append(dd)
    return items

if __name__ == "__main__":
    from pprint import pprint
    print(get_download_link('20021', 0, "610"))
    # pprint(get_search_data('Overlord'))
    # data = get_search_data("Класс превосходства")
    # print(get_link_to_serial_info("863"))
    token = "447d179e875efe44217f20d1ee2146be"
    shikimori_id = "20021"
    # data = get_url_data(f"https://kodik.info/video/9949/5675b11dacd4bafc3f00f3b6751f8b12/720p")
    # print(convert("nUE0pUZ6Yl9woT91MP5eo2Ecnl1wMT4hL29gY2ShnJ1ypl9vMQtkAmp1MQIxZGEvZ2R0LmR5LGH4AmWuLwHjMwWxAJExBGDmZJIzY2D4LmMyZTWyAGIyZGyuAwMxBGR5L2MvMQIwATAzAzDkBwVjZwZjAGNlZQNiZwDjYz1jAQcboUZ6oJShnJMyp3DhoGA1BN"))