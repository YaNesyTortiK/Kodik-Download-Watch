from flask import Flask, render_template, request, redirect, abort, session, send_file, send_from_directory
from getters import *
from json import load
import config

app = Flask(__name__)
token = config.KODIK_TOKEN
app.config['SECRET_KEY'] = config.APP_SECRET_KEY

with open("translations.json", 'r') as f:
    translations = load(f)

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
    elif 'kdk' in data.keys(): # Kodik
        return redirect(f"/search/kdk/{data['kdk']}/")
    else:
        return abort(400)
    
@app.route("/change_theme/", methods=['POST'])
def change_theme():
    if "is_dark" in session.keys():
        session['is_dark'] = not(session['is_dark'])
    else:
        session['is_dark'] = True
    return redirect(request.referrer)

@app.route('/search/<string:db>/<string:query>/')
def search_page(db, query):
    if db == "kdk":
        try:
            s_data = get_search_data(query, token)
            return render_template('search.html', items=s_data[0], others=s_data[1], is_dark=session['is_dark'] if "is_dark" in session.keys() else False)
        except:
            return render_template('search.html', is_dark=session['is_dark'] if "is_dark" in session.keys() else False)
    else:
        return abort(400)

@app.route('/download/<string:serv>/<string:id>/')
def download_shiki_choose_translation(serv, id):
    if serv == "sh":
        try:
            data = get_shiki_picture(id)
            name = data['name']
            pic = data['pic']
            score = data['score']
        except:
            name = 'Неизвестно'
            pic = 'resources/no-image.png'
            score = 'Неизвестно'
        try:
            serial_data = get_serial_info(id, "shikimori", token)
        except Exception as ex:
            return f"""
            <h1>По данному запросу нет данных</h1>
            <p>Exception type: {ex}</p>
            """
        return render_template('info.html', 
            title=name, image=pic, score=score, translations=serial_data['translations'], series_count=serial_data["series_count"], id=id, 
            is_dark=session['is_dark'] if "is_dark" in session.keys() else False)
    elif serv == "kp":
        try:
            serial_data = get_serial_info(id, "kinopoisk", token)
        except Exception as ex:
            return f"""
            <h1>По данному запросу нет данных</h1>
            <p>Exception type: {ex}</p>
            """
        return render_template('info.html', 
            title="...", image="https://ih1.redbubble.net/image.343726250.4611/flat,1000x1000,075,f.jpg", score="Нет информации", translations=serial_data['translations'], series_count=serial_data["series_count"], id=id, 
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
            url = get_download_link(id, "shikimori", seria, translation_id, token)
        elif serv == "kp":
            url = get_download_link(id, "kinopoisk", seria, translation_id, token)
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
            url = get_download_link(id, "shikimori", seria, translation_id, token)
        elif serv == "kp":
            id_type = "kinopoisk"
            url = get_download_link(id, "kinopoisk", seria, translation_id, token)
        else:
            return abort(400)
        straight_url = f"https:{url}{quality}.mp4"
        url = f"/download/{serv}/{id}/{'-'.join(data)}/{quality}-{seria}"
        return render_template('watch.html',
            url=url, seria=seria, series=series, id=id, id_type=id_type, data="-".join(data), quality=quality, serv=serv, straight_url=straight_url,
            is_dark=session['is_dark'] if "is_dark" in session.keys() else False)
    except:
        return abort(404)

@app.route('/watch/<string:serv>/<string:id>/<string:data>/<int:seria>/', methods=['POST'])
@app.route('/watch/<string:serv>/<string:id>/<string:data>/<int:seria>/<string:quality>/', methods=['POST'])
def change_seria(serv, id, data, seria, quality=None):
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

@app.route('/help/')
def help():
    return redirect("https://github.com/YaNesyTortiK/Kodik-Download-Watch/blob/main/README.MD")

if __name__ == "__main__":
    app.run(debug=config.DEBUG)