from flask import Flask, render_template, request, redirect, abort, session, send_file
from flask_socketio import SocketIO, send, emit, join_room, leave_room
from flask_mobility import Mobility
from getters import *
from fast_download import clear_tmp, fast_download, get_path
import watch_together
from json import load
import config
import os

app = Flask(__name__)
Mobility(app)
socketio = SocketIO(app)

token = config.KODIK_TOKEN
app.config['SECRET_KEY'] = config.APP_SECRET_KEY

with open("translations.json", 'r') as f:
    # Используется для указания озвучки при скачивании файла
    translations = load(f)

if config.USE_SAVED_DATA or config.SAVE_DATA:
    from cache import Cache
    ch = Cache(config.SAVED_DATA_FILE, config.SAVING_PERIOD, config.CACHE_LIFE_TIME)
ch_save = config.SAVE_DATA
ch_use = config.USE_SAVED_DATA

watch_manager = watch_together.Manager(config.REMOVE_TIME)

# Очистка tmp
clear_tmp()

@app.route('/')
def index():
    return render_template('index.html', is_dark=session['is_dark'] if "is_dark" in session.keys() else False)

@app.route('/', methods=['POST'])
def index_form():
    data = dict(request.form)
    if 'shikimori_id' in data.keys():
        return redirect(f"/download/sh/{data['shikimori_id']}/")
    if 'kinopoisk_id' in data.keys():
        return redirect(f"/download/kp/{data['kinopoisk_id']}/")
    elif 'kdk' in data.keys(): # kdk = Kodik
        return redirect(f"/search/kdk/{data['kdk']}/")
    else:
        return abort(400)
    
@app.route("/change_theme/", methods=['POST'])
def change_theme():
    # Костыль для смены темы
    if "is_dark" in session.keys():
        session['is_dark'] = not(session['is_dark'])
    else:
        session['is_dark'] = True
    return redirect(request.referrer)

@app.route('/search/<string:db>/<string:query>/')
def search_page(db, query):
    if db == "kdk":
        try:
            # Попытка получить данные с кодика
            s_data = get_search_data(query, token, ch if ch_save or ch_use else None)
            return render_template('search.html', items=s_data[0], others=s_data[1], is_dark=session['is_dark'] if "is_dark" in session.keys() else False)
        except:
            return render_template('search.html', is_dark=session['is_dark'] if "is_dark" in session.keys() else False)
    else:
        # Другие базы не поддерживаются (возможно в будующем будут)
        return abort(400)

@app.route('/download/<string:serv>/<string:id>/')
def download_shiki_choose_translation(serv, id):
    if serv == "sh":
        cache_used = False
        if ch_use and ch.is_id("sh"+id):
            # Проверка кеша на наличие данных
            cached = ch.get_data_by_id("sh"+id)
            name = cached['title']
            pic = cached['image']
            score = cached['score']
            dtype = cached['type']
            date = cached['date']
            status = cached['status']
            rating = cached['rating']
            if is_good_quality_image(pic):
                # Проверка что была сохранена картинка в полном качестве
                # (При поиске по шики, выдаются картинки в урезанном качестве)
                cache_used = True
        if not cache_used:
            try:
                # Попытка получить данные с шики
                data = get_shiki_data(id)
                name = data['title']
                pic = data['image']
                score = data['score']
                dtype = data['type']
                date = data['date']
                status = data['status']
                rating = data['rating']
            except:
                name = 'Неизвестно'
                pic = config.IMAGE_AGE_RESTRICTED
                score = 'Неизвестно'
            finally:
                if ch_save and not ch.is_id("sh"+id):
                    # Записываем данные в кеш если их там нет
                    ch.add_id("sh"+id, name, pic, score, data['status'] if data else "Неизвестно", data['date'] if data else "Неизвестно", data['type'] if data else "Неизвестно", data['rating'] if data else "Неизвестно")

        try:
            # Получаем данные о наличии переводов от кодика
            serial_data = get_serial_info(id, "shikimori", token)
        except Exception as ex:
            return f"""
            <h1>По данному запросу нет данных</h1>
            {f'<p>Exception type: {ex}</p>' if config.DEBUG else ''}
            """
        try:
            related = get_related(id, 'shikimori')
        except:
            related = []
        return render_template('info.html', 
            title=name, image=pic, score=score, translations=serial_data['translations'], series_count=serial_data["series_count"], id=id, 
            dtype=dtype, date=date, status=status, rating=rating, related=related,
            is_dark=session['is_dark'] if "is_dark" in session.keys() else False)
    elif serv == "kp":
        try:
            # Получаем данные о наличии переводов от кодика
            serial_data = get_serial_info(id, "kinopoisk", token)
        except Exception as ex:
            return f"""
            <h1>По данному запросу нет данных</h1>
            {f'<p>Exception type: {ex}</p>' if config.DEBUG else ''}
            """
        return render_template('info.html', 
            title="...", image=config.IMAGE_NOT_FOUND, score="...", translations=serial_data['translations'], series_count=serial_data["series_count"], id=id, 
            dtype="...", date="...", status="...",
            is_dark=session['is_dark'] if "is_dark" in session.keys() else False)
    else:
        return abort(400)

@app.route('/download/<string:serv>/<string:id>/<string:data>/')
def download_choose_seria(serv, id, data):
    data = data.split('-')
    series = int(data[0])
    return render_template('download.html', series=series, is_dark=session['is_dark'] if "is_dark" in session.keys() else False)

@app.route('/download/<string:serv>/<string:id>/<string:data>/<string:download_type>-<string:quality>-<int:seria>/')
def redirect_to_download(serv, id, data, download_type, quality, seria):
    data = data.split('-')
    translation_id = str(data[1])
    if download_type == 'fast':
        return redirect(f'/fast_download/{serv}-{id}-{seria}-{translation_id}-{quality}-{data[0]}/')
    try:
        if serv == "sh":
            if ch_use and ch.is_seria("sh"+id, translation_id, seria):
                # Получаме данные из кеша (если есть и используется)
                url = ch.get_seria("sh"+id, translation_id, seria)
            else:
                # Получаем данные с сервера
                url = get_download_link(id, "shikimori", seria, translation_id, token)
                if ch_save and not ch.is_seria("sh"+id, translation_id, seria):
                    # Записываем данные в кеш
                    try:
                        # Попытка записать данные к уже имеющимся данным
                        ch.add_seria("sh"+id, translation_id, seria, url)
                    except KeyError:
                        pass
        elif serv == "kp":
            if ch_use and ch.is_seria("kp"+id, translation_id, seria):
                # Получаем данные из кеша (если есть и используется)
                url = ch.get_seria("kp"+id, translation_id, seria)
            else:
                # Получаем данные с сервера
                url = get_download_link(id, "kinopoisk", seria, translation_id, token)
                if ch_save and not ch.is_seria("kp"+id, translation_id, seria):
                    # Записываем данные в кеш
                    try:
                        # Попытка записать данные к уже имеющимся данным
                        ch.add_seria("kp"+id, translation_id, seria, url)
                    except KeyError:
                        pass
        else:
            return abort(400)
        translation = translations[translation_id] if translation_id in translations else "Неизвестно"
        if seria == 0:
            return redirect(f"https:{url}{quality}.mp4:Перевод-{translation}:.mp4")
        else:
            return redirect(f"https:{url}{quality}.mp4:Серия-{seria}:Перевод-{translation}:.mp4")
    except Exception as ex:
        return abort(500, f'Exception: {ex}')

@app.route('/download/<string:serv>/<string:id>/<string:data>/watch-<int:num>/')
def redirect_to_player(serv, id, data, num):
    if data[0] == "0":
        return redirect(f'/watch/{serv}/{id}/{data}/0/')
    else:
        return redirect(f'/watch/{serv}/{id}/{data}/{num}/')

@app.route('/watch/<string:serv>/<string:id>/<string:data>/<int:seria>/<string:old_quality>/q-<string:quality>/')
@app.route('/watch/<string:serv>/<string:id>/<string:data>/<int:seria>/<string:old_quality>/<int:timing>/q-<string:quality>/')
def change_watch_quality(serv, id, data, seria, old_quality, quality, timing = None):
    return redirect(f"/watch/{serv}/{id}/{data}/{seria}/{quality}/{str(timing)+'/' if timing else ''}")

@app.route('/watch/<string:serv>/<string:id>/<string:data>/<int:seria>/q-<string:quality>/')
@app.route('/watch/<string:serv>/<string:id>/<string:data>/<int:seria>/q-<string:quality>/<int:timing>/')
def redirect_to_old_type_quality(serv, id, data, seria, quality, timing = 0):
    return redirect(f'/watch/{serv}/{id}/{data}/{seria}/{quality}/{str(timing)+'/' if timing else ''}')

@app.route('/watch/<string:serv>/<string:id>/<string:data>/<int:seria>/')
@app.route('/watch/<string:serv>/<string:id>/<string:data>/<int:seria>/<string:quality>/')
@app.route('/watch/<string:serv>/<string:id>/<string:data>/<int:seria>/<string:quality>/<int:timing>/')
def watch(serv, id, data, seria, quality = "720", timing = 0):
    try:
        data = data.split('-')
        series = int(data[0])
        translation_id = str(data[1])
        if serv == "sh":
            id_type = "shikimori"
            if ch_use and ch.is_seria("sh"+id, translation_id, seria):
                # Получаем данные из кеша (если есть и используется)
                url = ch.get_seria("sh"+id, translation_id, seria)
            else:
                # Получаем данные с сервера
                url = get_download_link(id, "shikimori", seria, translation_id, token)
                if ch_save and not ch.is_seria("sh"+id, translation_id, seria):
                    # Записываем данные в кеш
                    try:
                        ch.add_seria("sh"+id, translation_id, seria, url)
                    except KeyError:
                        pass
        elif serv == "kp":
            id_type = "kinopoisk"
            if ch_use and ch.is_seria("kp"+id, translation_id, seria):
                # Получаем данные из кеша (если есть и используется)
                url = ch.get_seria("kp"+id, translation_id, seria)
            else:
                # Получаем данные с сервера
                url = get_download_link(id, "kinopoisk", seria, translation_id, token)
                if ch_save and not ch.is_seria("kp"+id, translation_id, seria):
                    # Записываем данные в кеш
                    try:
                        ch.add_seria("kp"+id, translation_id, seria, url)
                    except KeyError:
                        pass
        else:
            return abort(400)
        straight_url = f"https:{url}{quality}.mp4" # Прямая ссылка
        url = f"/download/{serv}/{id}/{'-'.join(data)}/old-{quality}-{seria}" # Ссылка на скачивание через этот сервер
        return render_template('watch.html',
            url=url, seria=seria, series=series, id=id, id_type=id_type, data="-".join(data), quality=quality, serv=serv, straight_url=straight_url,
            allow_watch_together=config.ALLOW_WATCH_TOGETER,
            is_dark=session['is_dark'] if "is_dark" in session.keys() else False,
            timing=timing)
    except:
        return abort(404)

@app.route('/watch/<string:serv>/<string:id>/<string:data>/<int:seria>/', methods=['POST'])
@app.route('/watch/<string:serv>/<string:id>/<string:data>/<int:seria>/<string:quality>/', methods=['POST'])
def change_seria(serv, id, data, seria, quality=None):
    # Если использовалась форма для изменения серии
    try:
        new_seria = int(dict(request.form)['seria'])
    except:
        return abort(400)
    data = data.split('-')
    series = int(data[0])
    if new_seria > series or new_seria < 1:
        return abort(400, "Данная серия не существует")
    else:
        return redirect(f"/watch/{serv}/{id}/{'-'.join(data)}/{new_seria}{'/'+quality if quality != None else ''}")
    

# Watch Together ===================================================
@app.route('/create_room/', methods=['POST'])
def create_room():
    orig = request.referrer
    data = orig.split("/")
    if len(data) == 9:
        data[8] = 720
        data.append('')
    temp = data[-4].split('-')
    data = {
        'serv': data[-6],
        'id': data[-5],
        'series_count': int(temp[0]),
        'translation_id': temp[1],
        'seria': int(data[-3]),
        'quality': int(data[-2]),
        'pause': False,
        'play_time': 0,
    }
    rid = watch_manager.new_room(data)
    watch_manager.remove_old_rooms()
    return redirect(f"/room/{rid}/")

@app.route('/room/<string:rid>/', methods=["GET"])
def room(rid):
    if not watch_manager.is_room(rid):
        return abort(404)
    rd = watch_manager.get_room_data(rid)
    watch_manager.room_used(rid)
    try:
        id = rd['id']
        seria = rd['seria']
        series = rd['series_count']
        translation_id = str(rd['translation_id'])
        quality = rd['quality']
        if rd['serv'] == "sh":
            id_type = "shikimori"
            if ch_use and ch.is_seria("sh"+id, translation_id, seria):
                # Получаем данные из кеша (если есть и используется)
                url = ch.get_seria("sh"+id, translation_id, seria)
            else:
                # Получаем данные с сервера
                url = get_download_link(id, "shikimori", seria, translation_id, token)
                if ch_save and not ch.is_seria("sh"+id, translation_id, seria):
                    # Записываем данные в кеш
                    try:
                        ch.add_seria("sh"+id, translation_id, seria, url)
                    except KeyError:
                        pass
        elif rd['serv'] == "kp":
            id_type = "kinopoisk"
            if ch_use and ch.is_seria("kp"+id, translation_id, seria):
                # Получаем данные из кеша (если есть и используется)
                url = ch.get_seria("kp"+id, translation_id, seria)
            else:
                # Получаем данные с сервера
                url = get_download_link(id, "kinopoisk", seria, translation_id, token)
                if ch_save and not ch.is_seria("kp"+id, translation_id, seria):
                    # Записываем данные в кеш
                    try:
                        ch.add_seria("kp"+id, translation_id, seria, url)
                    except KeyError:
                        pass
        else:
            return abort(400)
        straight_url = f"https:{url}{quality}.mp4" # Прямая ссылка
        url = f"/download/{rd['serv']}/{id}/{series}-{translation_id}/{quality}-{seria}" # Ссылка на скачивание через этот сервер
        return render_template('room.html',
            url=url, seria=seria, series=series, id=id, id_type=id_type, data=f"{series}-{translation_id}", quality=quality, serv=rd['serv'], straight_url=straight_url,
            start_time=rd['play_time'],
            is_dark=session['is_dark'] if "is_dark" in session.keys() else False)
    except:
        return abort(500)

@app.route('/room/<string:rid>/', methods=["POST"])
def change_room_seria_form(rid):
    data = dict(request.form)['seria']
    rdata = watch_manager.get_room_data(rid)
    if data == '':
        pass
    rdata['seria'] = int(data)
    rdata['play_time'] = 0
    watch_manager.room_used(rid)
    socketio.send({"data": {"status": 'update_page', 'time': 0}}, to=rid)
    return redirect(f"/room/{rid}/")

@app.route('/room/<string:rid>/cs-<int:seria>/')
def change_room_seria(rid, seria):
    if not watch_manager.is_room(rid):
        return abort(400)
    rdata = watch_manager.get_room_data(rid)
    rdata['seria'] = seria
    rdata['play_time'] = 0
    watch_manager.room_used(rid)
    socketio.send({"data": {"status": 'update_page', 'time': 0}}, to=rid)
    return redirect(f"/room/{rid}/")

@app.route('/room/<string:rid>/cq-<int:quality>/')
def change_room_quality(rid, quality):
    if not watch_manager.is_room(rid):
        return abort(400)
    rdata = watch_manager.get_room_data(rid)
    rdata['quality'] = quality
    watch_manager.room_used(rid)
    socketio.send({"data": {"status": 'update_page', 'time': rdata['play_time']}}, to=rid)
    return redirect(f"/room/{rid}/")

@app.route('/fast_download_act/<string:id_type>-<string:id>-<int:seria_num>-<string:translation_id>-<string:quality>/')
@app.route('/fast_download_act/<string:id_type>-<string:id>-<int:seria_num>-<string:translation_id>-<string:quality>-<int:max_series>/')
def fast_download_work(id_type: str, id: str, seria_num: int, translation_id: str, quality: str, max_series: int = 12):
    from fast_download import fast_download, get_path
    translation = translations[translation_id] if translation_id in translations else "Неизвестно"
    add_zeros = len(str(max_series))
    fname = f'Перевод-{translation}-{quality}p' if seria_num == 0 else f'Серия-{str(seria_num).zfill(add_zeros)}-Перевод-{translation}-{quality}p'
    try:
        hsh = fast_download(id, id_type, seria_num, translation_id, quality, config.KODIK_TOKEN,
                            filename=fname)
        return send_file(get_path(hsh), as_attachment=True)
    except ModuleNotFoundError:
        return abort(500, 'Внимание, на сервере не установлен ffmpeg или программа не может получить к нему доступ. Ffmpeg обязателен для использования быстрой загрузки. (Стандартная загрузка работает без ffmpeg)')
    except FileNotFoundError:
        return abort(404, 'Видеофайл не найден, попробуйте сменить качество')

@app.route('/fast_download/<string:id_type>-<string:id>-<int:seria_num>-<string:translation_id>-<string:quality>/')
def fast_download_prepare(id_type: str, id: str, seria_num: int, translation_id: str, quality: str):
    return render_template('fast_download_prepare.html', 
                           url=f'/fast_download_act/{id_type}-{id}-{seria_num}-{translation_id}-{quality}/',
                           past_url=request.referrer if request.referrer else f'/download/{id_type}/{id}/',
                           is_dark=session['is_dark'] if "is_dark" in session.keys() else False)

# =======================================================================
# Sockets ====================================

@socketio.on('join')
def on_join(data):
    join_room(data['rid'])
    if not watch_manager.is_room(data['rid']):
        pass
    watch_manager.room_used(data['rid'])
    return send({'data': {'status': 'loading', 'time': watch_manager.get_room_data(data['rid'])['play_time']}}, to=data['rid'])

@socketio.on('broadcast')
def broadcast(data):
    watch_manager.room_used(data['rid'])
    watch_manager.update_play_time(data['rid'], data['data']['time'])
    return send(data, to=data['rid'])

#  ===========================================
# Shortcuts vvvv

@app.route('/help/')
def help():
    # Заглушка
    return redirect("https://github.com/YaNesyTortiK/Kodik-Download-Watch/blob/main/README.MD")

@app.route('/resources/<string:path>')
def resources(path: str):
    if os.path.exists(f'resources\\{path}'): # Windows-like
        return send_file(f'resources\\{path}')
    elif os.path.exists(f'resources/{path}'): # Unix
        return send_file(f'resources/{path}')
    else:
        return abort(404)

@app.route('/favicon.ico')
def favicon():
    return send_file(config.FAVICON_PATH)

if __name__ == "__main__":
    socketio.run(app, host=config.HOST, port=config.PORT, debug=config.DEBUG)
    