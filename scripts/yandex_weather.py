#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, urllib, math
from xml.etree import ElementTree


class YandexWeather():
    def __init__(self, location):
        self.yandex_ng = '{http://weather.yandex.ru/forecast}%s'
        self.weather_url = 'http://export.yandex.ru/weather-ng/forecasts/%s.xml' % (location)

        try:
            urllib.socket.setdefaulttimeout(8)
            usock = urllib.urlopen(self.weather_url)
            tree = ElementTree.parse(usock)
            usock.close()
        except:
            print 'ERROR - Current Conditions - Could not get information from server...'
            sys.exit(2)

        self.xml_root = tree.getroot()
        self.fact_city = self.xml_root.get('city')
        for fact in self.xml_root.iter(self.yandex_ng % 'fact'):
            self.fact_temperature = fact.find(self.yandex_ng % 'temperature').text
            self.fact_condition = fact.find(self.yandex_ng % 'weather_type').text
            self.fact_wind_direction = self._convert_wind_en2ru(fact.find(self.yandex_ng % 'wind_direction').text)
            self.fact_wind_speed = fact.find(self.yandex_ng % 'wind_speed').text

    def get_weather_by_hour(self):
        for day in self.xml_root.iter(self.yandex_ng % 'day'):
            condition = {}
            wind_direction = {}
            wind_speed = {}
            date = day.get('date')
            for day_part in day.iter(self.yandex_ng % 'day_part'):
                day_part_typeid = int(day_part.get('typeid'))
                condition[day_part_typeid] = day_part.find(self.yandex_ng % 'weather_type').text
                wind_direction[day_part_typeid] = self._convert_wind_en2ru(day_part.find(self.yandex_ng % 'wind_direction').text)
                wind_speed[day_part_typeid] = day_part.find(self.yandex_ng % 'wind_speed').text

            for hour in day.iter(self.yandex_ng % 'hour'):
                hour_at = int(hour.get('at'))
                tipeid = int(math.ceil(hour_at/4)+1)
                temperature = hour.find(self.yandex_ng % 'temperature').text
                yield {
                    'city': self.fact_city,
                    'date': date,
                    'hour_at': str(hour_at), 
                    'tipeid': tipeid, 
                    'temperature': temperature, 
                    'condition': condition[tipeid], 
                    'wind_direction': wind_direction[tipeid], 
                    'wind_speed': wind_speed[tipeid]
                }
                if hour_at == 23:
                    break
            break

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
        if value in dict_enru_wind_direction:
            value = dict_enru_wind_direction[value]
        return value

    def __unicode__(self):
        return u'%s: %s° C, %s, %s ветер %s м/с' % (self.fact_city, self.fact_temperature, self.fact_condition, self.fact_wind_direction, self.fact_wind_speed)


def main(location):
    weather = YandexWeather(location)
    for item in weather.get_weather_by_hour():
        print u'%s %s:00:00' % (item['date'], item['hour_at'].zfill(2))
        print u'%s %s:59:59' % (item['date'], item['hour_at'].zfill(2))
    print unicode(weather)

if __name__ == "__main__":
    location = '29997' # Аршан
    location = '30818' # Байкальск
    location = '30710' # Иркутск
    location = '30823' # Улан-Удэ
    location = '30715' # Ангарск
    location = '30405' # Братск
    sys.exit(main('30710'))
