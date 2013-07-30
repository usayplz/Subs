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
        'blowing sand': u'пе��ана� б���',
        'blowing snow': u'ме�ел�',
        'chance of rain': u'возможен дожд�',
        'chance of snow': u'возможен �нег',
        'chance of storm': u'��о�мовое п�ед�п�еждение',
        'chance of tstorm': u'��о�мовое п�ед�п�еждение',
        'clear': u'��но',
        'cloudy': u'обла�но',
        'drizzle': u'дожд�',
        'dust whirls': u'п�л�н�е ви��и',
        'dust': u'п�л�',
        'fog': u'��ман',
        'freezing drizzle': u'измо�оз�',
        'freezing rain': u'лед�ной дожд�',
        'hail showers': u'г�ад',
        'hail': u'г�ад',
        'haze': u'д�мка',
        'light snow': u'небол��ой �нег',
        'light rain': u'небол��ой дожд�',
        'mist': u'��ман',
        'mostly cloudy': u'пе�еменна� обла�но���',
        'mostly sunny': u'небол��а� обла�но���',
        'overcast': u'па�м��но',
        'partial fog': u'��ман',
        'partly cloudy': u'��но',
        'partly sunny': u'ме��ами �олне�но',
        'rain and snow': u'дожд� и �нег',
        'rain mist': u'дожд�, ��ман',
        'rain showers': u'дожд�',
        'rain': u'дожд�',
        'sand': u'пе�ок',
        'sandstorm': u'пе��ана� б���',
        'scattered clouds': u'возможен дожд�',
        'scattered showers': u'возможен дожд�',
        'scattered thunderstorms': u'возможен� г�оз�',
        'shallow fog': u'низкий ��ман',
        'showers': u'ливен�',
        'sleet': u'дожд� �о �негом',
        'smoke': u'д�м',
        'snow blowing snow mist': u'�нег ме�ел� ��ман ',
        'snow showers': u'�нег',
        'snow': u'�нег',
        'snow showers': u'�нег',
        'squalls': u'�квал�',
        'storm': u'б���',
        'sunny': u'�олне�но',
        'thunderstorm': u'г�оза',
        'thunderstorms and rain': u'г�оз� и дожд�',
        'thunderstorms and snow': u'г�оз� и �нег',
        'thunderstorms with hail': u'г�оз� � г�адом',
        'thunderstorms with small hail': u'г�оз� � г�адом небол��ие ',
        'unknown precipitation': u'о�адки',
        'volcanic ash': u'в�лкани�е�кий пепел',
        'widespread dust': u'п�л�',
    }
    return dict_enru_weather_direction[value]

# def __unicode__(self):
#     return u'%s: %s° C, %s, %s ветер %s м/с' % (self.city, self.temperature, self.weather, self.wind_direction, self.wind_speed)


def main(location):
#    yahoo_result = pywapi.get_weather_from_yahoo(location)
#    print yahoo_result
#    print "---------------------------------------------------------"
    weather_com_result = pywapi.get_weather_from_weather_com('RSXX8707')
    print weather_com_result['current_conditions']['temperature']
#    print _convert_weather_en2ru(
    print weather_com_result['current_conditions']['text']
    print _convert_wind_en2ru(weather_com_result['current_conditions']['wind']['text'])
    print _kph2mps(weather_com_result['current_conditions']['wind']['speed'])

    # weather = YahooWeather(location)
    # print unicode(weather)

if __name__ == "__main__":
    location = "1984174"
    exit(main(location))
