#!/usr/bin/env python
# -*- coding: utf-8 -*-

import  pywapi

def _kph2mps(value):
    """convert kilometer per hour to meter per second"""
    return int(value)*1000/3600

def _convert_wind_en2ru(value):
    dict_enru_wind_direction = {
        'East'  :   u'восточный',
        'ENE'   :   u'северо-восточный',
        'ESE'   :   u'юго-восточный',
        'NE'    :   u'северо-восточный',
        'NNE'   :   u'северо-восточный',
        'NNW'   :   u'северо-западный',
        'North' :   u'северный',
        'NW'    :   u'северо-западный',
        'SE'    :   u'юго-восточный',
        'South' :   u'южный',
        'SSE'   :   u'юго-восточный',
        'SSW'   :   u'юго-западный',
        'SW'    :   u'юго-западный',
        'Variable': u'переменный',
        'West'  :   u'западный',
        'WNW'   :   u'северо-западный',
        'WSW'   :   u'юго-западный',
    }
    return dict_enru_wind_direction[value]

def _convert_weather_en2ru(value):
    value = value.lower()
    dict_enru_weather_direction = {
        'blowing sand': u'песчаная буря',
        'blowing snow': u'метель',
        'chance of rain': u'возможен дождь',
        'chance of snow': u'возможен снег',
        'chance of storm': u'штормовое предупреждение',
        'chance of tstorm': u'штормовое предупреждение',
        'clear': u'ясно',
        'cloudy': u'облачно',
        'drizzle': u'дождь',
        'dust whirls': u'пыльные вихри',
        'dust': u'пыль',
        'fog': u'туман',
        'freezing drizzle': u'изморозь',
        'freezing rain': u'ледяной дождь',
        'hail showers': u'град',
        'hail': u'град',
        'haze': u'дымка',
        'light snow': u'небольшой снег',
        'light rain': u'небольшой дождь',
        'mist': u'туман',
        'mostly cloudy': u'переменная облачность',
        'mostly sunny': u'небольшая облачность',
        'overcast': u'пасмурно',
        'partial fog': u'туман',
        'partly cloudy': u'ясно',
        'partly sunny': u'местами солнечно',
        'rain and snow': u'дождь и снег',
        'rain mist': u'дождь, туман',
        'rain showers': u'дождь',
        'rain': u'дождь',
        'sand': u'песок',
        'sandstorm': u'песчаная буря',
        'scattered clouds': u'возможен дождь',
        'scattered showers': u'возможен дождь',
        'scattered thunderstorms': u'возможены грозы',
        'shallow fog': u'низкий туман',
        'showers': u'ливень',
        'sleet': u'дождь со снегом',
        'smoke': u'дым',
        'snow blowing snow mist': u'снег метель туман ',
        'snow showers': u'снег',
        'snow': u'снег',
        'snow showers': u'снег',
        'squalls': u'шквалы',
        'storm': u'буря',
        'sunny': u'солнечно',
        'thunderstorm': u'гроза',
        'thunderstorms and rain': u'грозы и дождь',
        'thunderstorms and snow': u'грозы и снег',
        'thunderstorms with hail': u'грозы с градом',
        'thunderstorms with small hail': u'грозы с градом небольшие ',
        'unknown precipitation': u'осадки',
        'volcanic ash': u'вулканический пепел',
        'widespread dust': u'пыль',
    }
    return dict_enru_weather_direction[value]

def main(location):
#    yahoo_result = pywapi.get_weather_from_yahoo(location)
#    print yahoo_result
#    print "---------------------------------------------------------"
    weather_com_result = pywapi.get_weather_from_weather_com(location)
    print weather_com_result['current_conditions']['temperature']
    print _convert_weather_en2ru(weather_com_result['current_conditions']['text'])
    print _convert_wind_en2ru(weather_com_result['current_conditions']['wind']['text'])
    print _kph2mps(weather_com_result['current_conditions']['wind']['speed'])

if __name__ == "__main__":
    location = "RSXX8707"
    exit(main(location))
