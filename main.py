import json
import telebot
import requests as req
from geopy import geocoders
from os import environ

token_bot = environ['token_bot']
token_accu = environ['token_accu']
token_yandex = environ['token_yandex']

bot = telebot.TeleBot(token_bot)

latitude = 0
longitude = 0

with open('cities.json', encoding='utf-8') as f:
    cities_list = json.load(f)
    print(cities_list)

def code_location(latitude: str, longitude: str, token_accu: str):
    url_location_key = 'https://dataservice.accuweather.com/locations/v1/cities/geoposition/search?apikey=' \
                       f'{token_accu}&q={latitude},{longitude}&language=ru'
    resp_loc = req.get(url_location_key, headers={"APIKey": token_accu})
    json_data = json.loads(resp_loc.text)
    code_loc = json_data['Key']
    return code_loc

def accu_weather(code_loc: str, token_accu: str):
    url_weather = f'http://dataservice.accuweather.com/forecasts/v1/hourly/12hour/{code_loc}?' \
                  f'apikey={token_accu}&language=ru&metric=True'
    response = req.get(url_weather, headers={"APIKey": token_accu})
    json_data = json.loads(response.text)
    dict_weather = dict()
    dict_weather['link'] = json_data[0]['MobileLink']
    time = 'сейчас'
    dict_weather[time] = {'temp': json_data[0]['Temperature']['Value'], 'sky': json_data[0]['IconPhrase']}
    for i in range(1, len(json_data)):
        time = 'через' + str(i) + 'ч'
        dict_weather[time] = {'temp': json_data[i]['Temperature']['Value'], 'sky': json_data[i]['IconPhrase']}
    return dict_weather

def print_weather(dict_weather, message):
    bot.send_message(message.chat.id, f'Данные о погоде:' +'\n'+ '\n'
                                           f'Температура сейчас {dict_weather["сейчас"]["temp"]}°C'+ '\n'
                                           f'  {dict_weather["сейчас"]["sky"]}.' + '\n'+ '\n'
                                           f'Температура через три часа {dict_weather["через3ч"]["temp"]}°C'+ '\n'
                                           f'  {dict_weather["через3ч"]["sky"]}.' + '\n'+ '\n'
                                           f'Температура через шесть часов {dict_weather["через6ч"]["temp"]}°C'+ '\n'
                                           f'  {dict_weather["через6ч"]["sky"]}.' + '\n'+ '\n'
                                           f'Температура через девять часов {dict_weather["через9ч"]["temp"]}°C'+ '\n'
                                           f'  {dict_weather["через9ч"]["sky"]}.' + '\n')
    bot.send_message(message.chat.id, f'По ссылке ниже доступен подробный прогноз ' +'\n'
                                           f'{dict_weather["link"]}')

def yandex_weather(latitude, longitude, token_yandex: str):
    url_yandex = f'http://api.weather.yandex.ru/v2/informers/?lat={latitude}&lon={longitude}&[lang=ru_RU]'
    yandex_req = req.get(url_yandex, headers={'X-Yandex-API-Key': token_yandex}, verify=True)
    conditions = {'clear': 'Ясно', 'partly-cloudy': 'Малооблачно', 'cloudy': 'Облачно с прояснениями',
                  'overcast': 'Пасмурно', 'drizzle': 'Морось', 'light-rain': 'Небольшой дождь',
                  'rain': 'Дождь', 'moderate-rain': 'Умеренно сильный дождь', 'heavy-rain': 'Сильный дождь',
                  'continuous-heavy-rain': 'Длительный сильный дождь', 'showers': 'Ливень',
                  'wet-snow': 'Дождь со снегом', 'light-snow': 'Небольшой снег', 'snow': 'Снег',
                  'snow-showers': 'Снегопад', 'hail': 'Град', 'thunderstorm': 'Гроза',
                  'thunderstorm-with-rain': 'Дождь с грозой', 'thunderstorm-with-hail': 'Гроза с градом'
                  }
    wind_dir = {'nw': 'северо-западное', 'n': 'северное', 'ne': 'северо-восточное', 'e': 'восточное',
                'se': 'юго-восточное', 's': 'южное', 'sw': 'юго-западное', 'w': 'западное', 'с': 'штиль'}

    yandex_json = json.loads(yandex_req.text)
    yandex_json['fact']['condition'] = conditions[yandex_json['fact']['condition']]
    yandex_json['fact']['wind_dir'] = wind_dir[yandex_json['fact']['wind_dir']]
    for parts in yandex_json['forecast']['parts']:
        parts['condition'] = conditions[parts['condition']]
        parts['wind_dir'] = wind_dir[parts['wind_dir']]

    weather = dict()
    params = ['condition', 'wind_dir', 'pressure_mm', 'humidity']
    for parts in yandex_json['forecast']['parts']:
        weather[parts['part_name']] = dict()
        weather[parts['part_name']]['temp'] = parts['temp_avg']
        for param in params:
            weather[parts['part_name']][param] = parts[param]

    weather['fact'] = dict()
    weather['fact']['temp'] = yandex_json['fact']['temp']
    for param in params:
        weather['fact'][param] = yandex_json['fact'][param]

    weather['link'] = yandex_json['info']['url']
    return weather

def print_yandex_weather(dict_weather_yandex, message):
    day = {'night': 'ночью', 'morning': 'утром', 'day': 'днем', 'evening': 'вечером', 'fact': 'сейчас'}
    bot.send_message(message.chat.id, f'По данным Яндекса:')
    for i in dict_weather_yandex.keys():
        if i != 'link':
            time_day = day[i]
            bot.send_message(message.chat.id, f'Температура {time_day} {dict_weather_yandex[i]["temp"]}°C' + '\n'
                                                   f'{dict_weather_yandex[i]["condition"]}')

    bot.send_message(message.chat.id, f' По ссылке ниже доступен подробный прогноз ' + '\n'
                                           f'{dict_weather_yandex["link"]}')

def geo_pos(city_name: str):
    global latitude
    global longitude
    geolocator = geocoders.Nominatim(user_agent="telebot")
    latitude = str(geolocator.geocode(city_name).latitude)
    longitude = str(geolocator.geocode(city_name).longitude)
    return latitude, longitude



def add_city(message):
    global cities_list
    lat, lon = geo_pos(message.text.lower().split('город ')[1])
    new_list = {str(message.from_user.id): {
        'city' :message.text.lower().split('город ')[1],
        'lat': lat,
        'lon': lon
        }
    }
    cities_list.update(new_list)
    with open('cities.json', 'w') as file:
        file.write(json.dumps(cities_list))
    return cities_list, 0


@bot.message_handler(command=['start'])
def send_welcome(message):
    bot.reply_to(message, f'Я бот погоды, приятно познакомиться, {message.from_user.first_name}')


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    if message.text.lower() == 'привет':
        bot.send_message(message.chat.id,
                         f'Здравствуйте, {message.from_user.first_name}! Я с удовольствием расскажу '
                         f' Вам о погоде! Напишите  слово "погода" и я напишу погоду в Вашем'
                         f' "стандартном" городе или напишите название города в котором Вы сейчас')
    elif message.text.lower() == 'погода':
        global cities_list
        if str(message.from_user.id) in cities_list.keys():
            city_name = cities_list[str(message.from_user.id)]['city']
            bot.send_message(message.chat.id, f'{message.from_user.first_name},'
                                              f' Твой город {city_name}')
            lat = cities_list[str(message.from_user.id)]['lat']
            lon = cities_list[str(message.from_user.id)]['lon']
            code_loc = code_location(lat, lon, token_accu)
            you_weather = accu_weather(code_loc, token_accu)
            print_weather(you_weather, message)
            yandex_weather_x = yandex_weather(lat, lon, token_yandex)
            print_yandex_weather(yandex_weather_x, message)
        else:
            bot.send_message(message.chat.id, f'Простите, Я не знаю такого города! '
                                              f'Просто напиши: "Мой город *****" '
                                              f'и я запомню твой стандартный город!')
    elif message.text.lower()[:9] == 'мой город':
        cities_list, flag = add_city(message)
        if flag == 0:
            bot.send_message(message.chat.id, f' Теперь я знаю Ваш город! Это'
                                              f' {cities_list[str(message.from_user.id)]["city"]}')
        else:
            bot.send_message(message.chat.id, f'К сожалению '
                                              f'что-то пошло не так :(')
    else:
        if message.text.lower() != '/start':
            try:
                city_name = message.text
                bot.send_message(message.chat.id, f'Привет {message.from_user.first_name}! Твой город {city_name}')
                lat, lon = geo_pos(city_name)
                print('Город: ' + city_name + '\n' + 'Lat: ' + lat + '\n' + 'Lon: ' + lon)
                code_loc = code_location(lat, lon, token_accu)
                you_weather = accu_weather(code_loc, token_accu)
                print_weather(you_weather, message)
                yandex_weather_x = yandex_weather(lat, lon, token_yandex)
                print_yandex_weather(yandex_weather_x, message)
            except AttributeError as err:
                bot.send_message(message.chat.id, f'Простите, {message.from_user.first_name}, '
                                                  f'Я не нашел такого города '
                                                  f'и получил ошибку {err}, попробуй другой город')
        else:
            send_welcome(message)



bot.infinity_polling()
