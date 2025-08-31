from hashlib import md5
from getters import get_download_link, get_url_data
import requests
import os
import threading
import subprocess

def fast_download(id: str, id_type: str, seria_num: int, translation_id: str, quality: str, token: str, filename: str = 'result', metadata: dict = {}) -> str:
    """
    Эта функция обеспечивает быструю загрузку засчет параллельной загрузки нескольких фрагментов.
    :id: Id сериала на Шикимори/Кинопоиске
    :id_type: тип id 'shikimori' или 'kinopoisk' ('sh' или 'kp')
    :seria_num: номер серии
    :translation_id: id переода/субтитров (Прим: 640 - Anilibria.TV)
    :token: Токен Kodik

    Возвращает хэш значение по которому можно получить путь до файла с результатом
    """
    check_ffmpeg() # Проверка на досутпность ffmpeg из модуля subprocess
    hsh = md5(str(id+id_type+translation_id+str(seria_num)+quality).encode('utf-8')).hexdigest()+"~"
    if not os.path.exists('tmp/'):
        os.mkdir('tmp')
    try:
        os.mkdir(f'tmp/{hsh}')
    except FileExistsError:
        if len(list(x for x in os.listdir(f'tmp/{hsh}/') if x[x.rfind('.')+1:] == 'mp4')) > 0:
            return hsh # Если уже есть скачанный и собранный результат для этого хэша
        else:
            for h in os.listdir(f'tmp/{hsh}'): # Очищаем кеш
                os.remove(f'tmp/{hsh}/{h}')
    
    if id_type == 'sh': id_type = 'shikimori'
    elif id_type == 'kp': id_type = 'kinopoisk'
    link = get_download_link(id, id_type, seria_num, translation_id, token)
    manifest = get_url_data('https:'+link+quality+'.mp4:hls:manifest.m3u8')
    segments = get_segments(manifest, 'https:'+link)
    thr = len(segments)
    threads = []
    for i in range(thr):
        threads.append(threading.Thread(target=download_segment, args=(segments[i][0], 'tmp/'+hsh+'/'+segments[i][1]+'.ts')))
    for x in threads:
        x.start()
    for x in threads:
        x.join()
    combine_segments('tmp/'+hsh+'/', segments_count=len(segments), name=filename.replace(' ', '-'), metadata=metadata)
    return hsh

def get_segments(manifest: str, original_link: str) -> list[str]:
    res = []
    manifest = manifest.split('\n')[7:]
    for i in range(0, len(manifest), 2):
        if manifest[i].strip() != '':
            res.append([original_link+manifest[i][2:], manifest[i].split('-')[1]])
    return res

def download_segment(link: str, path: str):
    try:
        res = requests.get(link)
    except requests.exceptions.SSLError:
        # Sometimes this error can appear. Possibly because of high count of downloads at the same time
        res = requests.get(link)
    with open(path, 'wb') as f:
        f.write(res.content)

def combine_segments(directory: str, segments_count: int, name: str = 'result', metadata: dict = {}, hwaccel: str|None = 'cuda'):
    files = list(x for x in os.listdir(directory) if x[x.rfind('.')+1:] == 'ts')
    r = ''
    for file in sorted(files, key=lambda x: int(x[:-3])):
        if file[file.rfind('.')+1:] == 'ts':
            r += "file '"+file+"'\n"
    with open(directory+'files.txt', 'w') as f:
        f.write(r)
    metadata_str = ''.join(f'-metadata {k}="{v}" ' for k,v in metadata.items())
    subprocess.call(f'ffmpeg -y{" -hwaccel " + hwaccel if not hwaccel is None else "" } -f concat -safe 0 -i {directory}files.txt -c copy {metadata_str} {directory}{name}.mp4', stderr=subprocess.DEVNULL)

def get_path(hsh: str) -> str:
    if os.path.exists(f'tmp\\{hsh}\\'):
        x = list(f'tmp\\{hsh}\\'+x for x in os.listdir(f'tmp/{hsh}/') if x[x.rfind('.')+1:] == 'mp4')
        if len(x) > 0:
            return x[0]
        else:
            raise FileNotFoundError(f'Result .mp4 file not found in "{hsh}" directory')
    elif os.path.exists(f'tmp/{hsh}/'):
        x = list(f'tmp/{hsh}/'+x for x in os.listdir(f'tmp/{hsh}/') if x[x.rfind('.')+1:] == 'mp4')
        if len(x) > 0:
            return x[0]
        else:
            raise FileNotFoundError(f'Result .mp4 file not found in "{hsh}" directory')
    else:
        raise FileNotFoundError(f'Temporary directory with hash "{hsh}" not found')

def check_ffmpeg():
    """
    Raises ModuleNotFound error if ffmpeg isn't installed or can't be used by subprocess
    """
    try:
        subprocess.call('ffmpeg', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        raise ModuleNotFoundError('Ffmpeg is required to use fast download.')
    
def clear_tmp():
    """
    Clears tmp direcory (Creates if not found). Use on the start of application.
    """
    if not os.path.exists('tmp'):
        os.mkdir('tmp')
    for x in os.listdir('tmp'):
        for h in os.listdir(f'tmp/{x}'):
            os.remove(f'tmp/{x}/{h}')
        os.rmdir(f'tmp/{x}')