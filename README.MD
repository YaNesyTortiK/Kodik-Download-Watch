<div align="center">
  <img src="resources/A.ico" alt="Logo" width="80" height="80">

  <h1 align="center">anime-site</h1>

  <p align="center">
    Небольшое Flask приложение для скачивания и просмотра аниме/дорам из базы Kodik.
    <br />
    <a href="https://github.com/1Dradon1/anime-site"><strong>Просмотреть репозиторий »</strong></a>
    <br />
    <br />
    <a href="#совместный-просмотр">Совместный просмотр</a>
    ·
    <a href="#shortcuts">Горячие клавиши</a>
    ·
    <a href="#настройка-конфигурации">Настройка</a>
  </p>

  <p align="center">
    <img src="https://img.shields.io/badge/Python-3.10.11%2B-blue?style=for-the-badge&logo=python" alt="Python">
    <img src="https://img.shields.io/badge/Flask-Framework-red?style=for-the-badge&logo=flask" alt="Flask">
    <img src="https://img.shields.io/badge/SocketIO-Realtime-white?style=for-the-badge&logo=socket.io" alt="SocketIO">
    <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License">
  </p>
</div>

---

## Описание

**anime-site** — это легкое веб-приложение на Flask, предназначенное для удобного поиска, просмотра и скачивания контента из базы Kodik. Главная особенность — возможность создавать комнаты для совместного просмотра с друзьями в реальном времени.

### Основные возможности
* **Поиск:** Гибкий поиск по базе Kodik, а также через ID Shikimori и Кинопоиск.
* **Совместный просмотр:** Создание публичных комнат для синхронного просмотра.
* **Загрузка:** Предзагрузка серий с использованием ffmpeg.
* **Адаптивность:** Удобный интерфейс для различных устройств.
* **Shortcuts:** Горячие клавиши для управления плеером.

---

## Как запустить

### Требования
* Python >= 3.10.11
* ffmpeg (необязательно, для быстрой загрузки)

### Установка

1. **Склонируйте репозиторий:**
   ```bash
   git clone https://github.com/1Dradon1/anime-site.git
   cd anime-site
   ```

2. **Создайте виртуальное окружение и файл для кэша:**
   * **Windows:**
     ```bash
     python -m venv venv
     venv\Scripts\activate
     echo {} > cache.json
     ```
   * **Linux:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     echo {} > cache.json
     ```

3. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Запуск:**
   ```bash
   python main.py
   ```
   Перейдите по адресу `http://127.0.0.1:5555` в вашем браузере.

---

## Настройка конфигурации

Все настройки производятся в файле `config.py`.

| Параметр | По умолчанию | Описание |
| :--- | :--- | :--- |
| `APP_SECRET_KEY` | - | Секретный ключ приложения |
| `SAVE_DATA` | `True` | Сохранять ли данные поиска в кэш |
| `USE_SAVED_DATA` | `True` | Использовать ли кэш при поиске |
| `SAVED_DATA_FILE` | `"cache.json"` | Файл для хранения кэша |
| `SAVING_PERIOD` | `5` | Период перезаписи данных (мин) |
| `CACHE_LIFE_TIME` | `3` | Время жизни кэша (дней) |
| `KODIK_TOKEN` | `None` | Ваш токен Kodik (автоопределение если `None`) |
| `ALLOW_WATCH_TOGETHER` | `True` | Включить функцию "Смотреть вместе" |
| `ALLOW_NSFW` | `True` | Использовать Shikimori API для обхода возрастных фильтров |
| `HOST` | `"0.0.0.0"` | IP адрес сервера |
| `PORT` | `5000` | Порт сервера |

> [!IMPORTANT]
> Если `KODIK_TOKEN` установлен в `None`, программа попытается найти его автоматически. В случае неудачи поиск будет перенаправлен через Shikimori API.

---

## Shortcuts

Горячие клавиши для управления встроенным плеером:

| Клавиша | Действие |
| :---: | :--- |
| `f` | Вход/выход из полноэкранного режима |
| `m` | Вкл/выкл звук |
| `d` | Перемотка вперед на 1:20 |
| `a` | Перемотка назад на 1:20 |
| `j` | Предыдущая серия |
| `l` | Следующая серия |

*Примечание: шорткаты отключены в режиме совместного просмотра.*

---

## Совместный просмотр

Функция реализована с использованием **WebSocket (Flask-SocketIO)**.
Позволяет синхронизировать действия всех участников комнаты:
- Пауза / Воспроизведение
- Перемотка
- Смена серии или качества

Примерная задержка синхронизации — менее 1 секунды.

---

## Поиск по ID

<details>
<summary><b>Как узнать ID на Shikimori?</b></summary>

1. Зайдите на [Shikimori](https://shikimori.one).
2. Найдите нужный тайтл.
3. ID находится в URL: `https://shikimori.one/animes/z20-naruto` -> `z20`.
</details>

<details>
<summary><b>Как узнать ID на Кинопоиск?</b></summary>

1. Зайдите на [Кинопоиск](https://www.kinopoisk.ru).
2. Найдите нужный сериал/фильм.
3. ID находится в URL: `https://www.kinopoisk.ru/series/749374/` -> `749374`.
</details>

---

## Лицензия

Распространяется под лицензией MIT. Подробности в файле [LICENSE](LICENSE).

## Thanks

- [YaNesyTortiK](https://github.com/YaNesyTortiK/) - [Kodik-Download-Watch](https://github.com/YaNesyTortiK/Kodik-Download-Watch)
- [bloc97](https://github.com/bloc97/) - [Anime4k](https://github.com/bloc97/Anime4K)<br>
also
- [D4mnedLure](https://github.com/D4mnedLure/) - for fixing bugs and huge UI improvements

<p align="right">(<a href="#top">наверх</a>)</p>
