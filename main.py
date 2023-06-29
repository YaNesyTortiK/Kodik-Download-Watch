from flask import Flask, render_template, request, redirect, abort, session, send_file
from flask_mobility import Mobility
from getters import *
import watch_together
from json import load
import config

app = Flask(__name__)
Mobility(app)

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
            except:
                name = 'Неизвестно'
                pic = config.IMAGE_AGE_RESTRICTED
                score = 'Неизвестно'
            finally:
                if ch_save and not ch.is_id("sh"+id):
                    # Записываем данные в кеш если их там нет
                    ch.add_id("sh"+id, name, pic, score, data['status'] if data else "Неизвестно", data['date'] if data else "Неизвестно", data['type'] if data else "Неизвестно", )

        try:
            # Получаем данные о наличии переводов от кодика
            serial_data = get_serial_info(id, "shikimori", token)
        except Exception as ex:
            return f"""
            <h1>По данному запросу нет данных</h1>
            {f'<p>Exception type: {ex}</p>' if config.DEBUG else ''}
            """
        return render_template('info.html', 
            title=name, image=pic, score=score, translations=serial_data['translations'], series_count=serial_data["series_count"], id=id, 
            dtype=dtype, date=date, status=status,
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

@app.route('/download/<string:serv>/<string:id>/<string:data>/<string:data2>/')
def redirect_to_download(serv, id, data, data2):
    data = data.split('-')
    translation_id = str(data[1])
    data2 = data2.split('-')
    quality = data2[0]
    seria = int(data2[1])
    try:
        if serv == "sh":
            if ch_use and ch.is_seria("sh"+id, translation_id, seria):
                # Получаем данные из кеша (если есть и используется)
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
        if seria == 0:
            return redirect(f"https:{url}{quality}.mp4:Перевод-{translations[translation_id]}:.mp4")
        else:
            return redirect(f"https:{url}{quality}.mp4:Серия-{seria}:Перевод-{translations[translation_id]}:.mp4")
    except Exception as ex:
        return abort(500, f'Exception: {ex}')

@app.route('/download/<string:serv>/<string:id>/<string:data>/watch-<int:num>/')
def redirect_to_player(serv, id, data, num):
    if data[0] == "0":
        return redirect(f'/watch/{serv}/{id}/{data}/0/')
    else:
        return redirect(f'/watch/{serv}/{id}/{data}/{num}/')

@app.route('/watch/<string:serv>/<string:id>/<string:data>/<int:seria>/<string:old_quality>/<string:quality>/')
def change_watch_quality(serv, id, data, seria, old_quality = None, quality = None):
    return redirect(f"/watch/{serv}/{id}/{data}/{seria}/{quality}/")

@app.route('/watch/<string:serv>/<string:id>/<string:data>/<int:seria>/')
@app.route('/watch/<string:serv>/<string:id>/<string:data>/<int:seria>/<string:quality>/')
def watch(serv, id, data, seria, quality = None):
    if quality == None:
        quality = "720"
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
        url = f"/download/{serv}/{id}/{'-'.join(data)}/{quality}-{seria}" # Ссылка на скачивание через этот сервер
        return render_template('watch.html',
            url=url, seria=seria, series=series, id=id, id_type=id_type, data="-".join(data), quality=quality, serv=serv, straight_url=straight_url,
            is_dark=session['is_dark'] if "is_dark" in session.keys() else False)
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
    

# Watch Together Part ===================================================

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
        'play_time': 0
    }
    print(data)
    rid = watch_manager.new_room(data)
    return redirect(f"/room/{rid}/")

@app.route('/room/<string:rid>/', methods=["GET"])
def room(rid):
    rd = watch_manager.get_room_data(rid)
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
    # return {"rid": rid, "data": watch_manager.get_room_data(rid)}

@app.route('/synchronize/<string:rid>/', methods=['POST'])
def synchronize(rid):
    data = dict(request.json)
    rdata = watch_manager.get_room_data(rid)
    # print("\tBef:", data, rdata, sep='\n')
    if data['clicked']:
        rdata['pause'] = data['pause']
        rdata['play_time'] = data['play_time']
        watch_manager.update_room(rid, rdata)
    else:
        watch_manager.room_used(rid)
    return rdata
    

# =======================================================================


@app.route('/help/')
def help():
    # Заглушка
    return redirect("https://github.com/YaNesyTortiK/Kodik-Download-Watch/blob/main/README.MD")

@app.route('/resources/<string:path>')
def resources(path: str):
    return send_file(f'resources\\{path}')

@app.route('/favicon.ico')
def favicon():
    return send_file(config.FAVICON_PATH)

if __name__ == "__main__":
    app.run(debug=config.DEBUG)