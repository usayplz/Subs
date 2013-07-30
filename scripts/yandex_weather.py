#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, urllib
from xml.etree import ElementTree


class YandexWeather():
    def __init__(self, location):
        try:
            weather_url = 'http://export.yandex.ru/weather-ng/forecasts/%s.xml' % (location)
            urllib.socket.setdefaulttimeout(8)
            usock = urllib.urlopen(weather_url)
            tree = ElementTree.parse(usock)
            usock.close()
        except:
            print 'ERROR - Current Conditions - Could not get information from server...'
            sys.exit(2)

        yandex_ng = '{http://weather.yandex.ru/forecast}%s'
        root = tree.getroot()
        self.city = root.get('city')
        for child in root.iter(yandex_ng % 'fact'):
            self.temperature = child.find(yandex_ng % 'temperature').text
            self.condition = child.find(yandex_ng % 'weather_type').text
            self.wind_direction = child.find(yandex_ng % 'wind_direction').text
            self.wind_speed = child.find(yandex_ng % 'wind_speed').text

        self.wind_direction = self._convert_wind_en2ru(self.wind_direction)

    def _convert_wind_en2ru(self, value):
        value = value.lower()
        dict_enru_wind_direction = {
            'east'  :   u'восточный',
            'e'     :   u'восточный',
            'ene'   :   u'северо-восточный',
            'ese'   :   u'юго-восточный',
            'ne'    :   u'северо-восточный',
            'nne'   :   u'северо-восточный',
            'nnw'   :   u'северо-западный',
            'north' :   u'северный',
            'n'     :   u'северный',
            'nw'    :   u'северо-западный',
            'se'    :   u'юго-восточный',
            'south' :   u'южный',
            's'     :   u'южный',
            'sse'   :   u'юго-восточный',
            'ssw'   :   u'юго-западный',
            'sw'    :   u'юго-западный',
            'variable': u'переменный',
            'west'  :   u'западный',
            'w'     :   u'западный',
            'wnw'   :   u'северо-западный',
            'wsw'   :   u'юго-западный',
        }
        return dict_enru_wind_direction[value]

    def __unicode__(self):
        weather = u'%s: %s° C, %s, %s ветер %s м/с' % (self.city, self.temperature, self.condition, self.wind_direction, self.wind_speed)
        return weather


def main(location):
    weather = YandexWeather(location)
    print unicode(weather)

if __name__ == "__main__":
    location = '29997' # Аршан
    location = '30818' # Байкальск
    location = '30710' # Иркутск
    location = '30823' # Улан-Удэ
    location = '30715' # Ангарск
    location = '30405' # Братск
    sys.exit(main(location))
