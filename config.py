KODIK_TOKEN = "447d179e875efe44217f20d1ee2146be"
APP_SECRET_KEY = "some_super_ultra_unbelievable_key"
DEBUG = False # Debug от Flask
SAVE_DATA = False # Для сохранения результатов парсинга (картинки, названия, ссылки на видео)
USE_SAVED_DATA = False # Для использования уже сохранённых результатов
SAVED_DATA_FILE = "cache.json" # Файл с сохранёнными данными (если SAVE_DATA == False и USE_SAVED_DATA == False, файл не обязателен)
SAVING_PERIOD = 10 # (В минутах) Как часто будет перезаписываться файл с сохранёнными данными
                   # Сохранение будет производиться только при условии что пользователь воспользовался сайтом
CACHE_LIFE_TIME = 1 # (В днях) Как часто будет обновляться информация в базе

IMAGE_NOT_FOUND = "https://ih1.redbubble.net/image.343726250.4611/flat,1000x1000,075,f.jpg" # Картинка для замены ненайденной
IMAGE_AGE_RESTRICTED = "https://e7.pngegg.com/pngimages/437/942/png-clipart-graphics-car-park-parking-signage-no-symbol-illegal-gambling-statement.png" # Картинка для обозначения контента с ограничениями по возрасту