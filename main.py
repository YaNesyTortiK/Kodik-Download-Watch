from flask import Flask, render_template, request, redirect, abort
from getters import *

app = Flask(__name__)
token = "447d179e875efe44217f20d1ee2146be"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def index_form():
    data = dict(request.form)
    if 'shikimori_id' in data.keys():
        return redirect(f"/download/shikimori/{data['shikimori_id']}/")
    elif 'kdk' in data.keys(): # Kodik
        return redirect(f"/search/kdk/{data['kdk']}")
    else:
        return abort(400)

@app.route('/search/<string:db>/<string:query>')
def search_page(db, query):
    if db == "kdk":
        try:
            s_data = get_search_data(query, token)
            return render_template('search.html', items=s_data)
        except:
            return render_template('search.html')
    else:
        return abort(400)

@app.route('/download/<string:id>/')
def download_shiki_choose_translation(id):
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
        serial_data = get_shiki_serial_info(id, token)
    except Exception as ex:
        return f"""
        <h1>По данному запросу нет данных</h1>
        <p>Exception type: {ex}</p>
        """
    return render_template('info.html', 
        title=name, image=pic, score=score, translations=serial_data['translations'], series_count=serial_data["series_count"], id=id)

@app.route('/download/<string:id>/<string:data>/')
def download_choose_seria(id, data):
    data = data.split('-')
    series = int(data[0])
    return render_template('download.html', series=series)

@app.route('/download/<string:id>/<string:data>/<string:data2>')
def redirect_to_download(id, data, data2):
    data = data.split('-')
    translation_id = str(data[1])
    data2 = data2.split('-')
    quality = data2[0]
    seria = int(data2[1])
    try:
        url = get_download_link(id, seria, translation_id, token)
        return redirect(f"https:{url}{quality}.mp4")
    except Exception as ex:
        return abort(500, f'Exception: {ex}')

@app.route('/download/<string:id>/<string:data>/watch-<int:num>/')
def redirect_to_player(id, data, num):
    if data[0] == "0":
        return redirect(f'/watch/{id}/{data}/0')
    else:
        return redirect(f'/watch/{id}/{data}/{num}')

@app.route('/watch/<string:id>/<string:data>/<int:seria>/')
@app.route('/watch/<string:id>/<string:data>/<int:seria>/<string:quality>')
def watch(id, data, seria, quality = None):
    if quality == None:
        quality = "720"
    try:
        data = data.split('-')
        series = int(data[0])
        translation_id = str(data[1])
        url = "https:"+get_download_link(id, seria, translation_id, token)+quality+".mp4"
        return render_template('watch.html',
            url=url, seria=seria, series=series, id=id, data="-".join(data), quality=quality)
    except:
        return abort(404)

@app.route('/watch/<string:id>/<string:data>/<int:seria>/', methods=['POST'])
def change_seria(id, data, seria):
    try:
        new_seria = int(dict(request.form)['seria'])
    except:
        return abort(400)
    data = data.split('-')
    series = int(data[0])
    if new_seria > series or new_seria < 1:
        return abort(400, "Данная серия не существует")
    else:
        return redirect(f"/watch/{id}/{'-'.join(data)}/{new_seria}")

@app.route('/help/')
def help():
    return redirect("https://github.com/YaNesyTortiK/Kodik-Download-Watch/blob/main/README.MD")

if __name__ == "__main__":
    app.run(debug=True)