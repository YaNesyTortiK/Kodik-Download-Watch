# Kodik-Download-Watch

## Описание
Небольшое Flask приложение для скачивания и просмотра аниме/дорам из базы Kodik

## Технологии
* Python
* Flask
* BeautifulSoup4
* Jinja2

## Как запустить

1. Склонируйте репозиторий
2. Создайте и активируйте виртуальное окружение
```commandline
python -m venv venv
venv/Scripts/activate
```  
3. Установите зависимости
```commandline
pip install -r requirements.txt
```
4. Измените APP_SECRET_KEY в файле config.py
5. Запустите файл main.py
```commandline
python main.py
```
## Как пользоваться сайтом

1. Найдите требуемый тайтл/сериал/фильм:
- Через поиск по базе Kodik (займёт некоторое время для обработки)
- Через поиск по id шикимори (подробную инструкцию см. ниже)
- Через поиск по id кинопоиска (подробную инструкцию см. ниже)

2. Выберите озвучку
3. Выберите серию для просмотра/загрузки

## Важные особенности
- Если при попытке загрузки возникает ошибка 404, попробуйте выбрать другое качество видео (т.к. некоторые более старые видео могут быть ниже 720p)
- Если при попытке просмотра видео будет не найдено, также попробуйте изменить качество
- Для ускорения работы программы фильмы и сериалы не имеющие shikimori id в базе Kodik'а будут без постеров и доп. информации

## Как узнать id тайтла на Шикимори
1. Зайдите на сайт <a href='shikimori.one'>Шикимори</a> и найдите там страницу требуемого сезона/фильма.
2. В адресной строке браузера будет виден id
- Примеры: <p>
    https://shikimori.me/animes/z20-naruto<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;^^^<br>
    В данном случае id будет "z20"<br><br>
    https://shikimori.me/animes/29803-overlord<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;^^^^^<br>
    В данном случае id будет "29803"</p>
3. Теперь можно подставлять полученный id в соответствующую поисковую строку

## Как узнать id тайтла на Кинопоиске
1. Зайдите на сайт <a href='https://www.kinopoisk.ru'>Кинопоиска</a> и найдите там страницу требуемого сериала/фильма.
2. В адресной строке браузера будет виден id
- Примеры: <p>
    https://www.kinopoisk.ru/series/749374/<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;^^^^^<br>
    В данном случае id будет "749374"<br><br>
    https://www.kinopoisk.ru/series/1220920/<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;^^^^^<br>
    В данном случае id будет "1220920"</p>
3. Теперь можно подставлять полученный id в соответствующую поисковую строку

### Про токен
Данный токен был найден в открытых источниках. Для его изменения в файле config.py измените соответствующую строку