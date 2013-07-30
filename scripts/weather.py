#!/usr/bin/env python
# -*- coding: utf-8 -*-

import  pywapi

def _kph2mps(self, value):
    """convert kilometer per hour to meter per second"""
    return int(value)*1000/3600

def _convert_wind_en2ru(self, value):
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

# def __unicode__(self):
#     return u'%s: %s° C, %s, %s ветер %s м/с' % (self.city, self.temperature, self.weather, self.wind_direction, self.wind_speed)


def main(location):
    yahoo_result = pywapi.get_weather_from_yahoo(location)
    print yahoo_result
    print "---------------------------------------------------------"
    weather_com_result = pywapi.get_weather_from_weather_com('RSXX8707:1')
    print weather_com_result
    # weather = YahooWeather(location)
    # print unicode(weather)

if __name__ == "__main__":
    location = "1984174"
    exit(main(location))
