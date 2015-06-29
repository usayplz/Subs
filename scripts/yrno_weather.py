#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, urllib, math
from xml.etree import ElementTree


class yrnoWeather():
    def __init__(self, location=None):
        self.weather_url = 'http://www.yr.no/place/%s/forecast.xml' % (location)
        self.fact_temperature = ''
        self.fact_condition = ''
        self.fact_wind_direction = ''
        self.fact_wind_speed = ''
        self.fact_pressure = ''
        if not location:
            return

        try:
            urllib.socket.setdefaulttimeout(8)
            usock = urllib.urlopen(self.weather_url)
            tree = ElementTree.parse(usock)
            usock.close()
        
            self.xml_root = tree.getroot()
            self.fact_city = self.xml_root.find('location/name').text
            for time in self.xml_root.iter('time'):
                self.fact_temperature = time[4].get('value')
                self.fact_condition = self._convert_condition_en2ru(time[0].get('name'))
                self.fact_wind_direction = self._convert_wind_en2ru_short(time[2].get('code'))
                self.fact_wind_speed = int(float(time[3].get('mps')))
                self.fact_pressure = int(float(time[5].get('value'))/1.333)
                break
        except:
            return 

    def get_weather_by_hour(self, location):
        self.weather_url = 'http://www.yr.no/place/%s/forecast_hour_by_hour.xml' % (location)
        try:
            urllib.socket.setdefaulttimeout(8)
            usock = urllib.urlopen(self.weather_url)
            tree = ElementTree.parse(usock)
            usock.close()
        
            self.xml_root = tree.getroot()
            city = self.xml_root.find('location/name').text
            for time in self.xml_root.iter('time'):
                temperature = time[4].get('value')
                condition = self._convert_condition_en2ru(time[0].get('name'))
                wind_direction = self._convert_wind_en2ru_short(time[2].get('code'))
                wind_speed = int(float(time[3].get('mps')))
                pressure = int(float(time[5].get('value'))/1.333)
                yield {
                    'city': city,
                    'time_from': time.get('from'),
                    'time_to': time.get('to'),
                    'temperature': temperature, 
                    'condition': condition, 
                    'wind_direction': wind_direction, 
                    'wind_speed': wind_speed,
                    'pressure': pressure
                }
        except:
            return

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

    def _convert_wind_en2ru_short(self, value):
        value = value.lower()
        dict_enru_wind_direction = {
            'east'  :   u'В',
            'e'     :   u'В',
            'ene'   :   u'СВ',
            'ese'   :   u'ЮВ',
            'ne'    :   u'СВ',
            'nne'   :   u'СВ',
            'nnw'   :   u'СЗ',
            'north' :   u'С',
            'n'     :   u'С',
            'nw'    :   u'СЗ',
            'se'    :   u'ЮВ',
            'south' :   u'Ю',
            's'     :   u'Ю',
            'sse'   :   u'ЮВ',
            'ssw'   :   u'ЮЗ',
            'sw'    :   u'ЮЗ',
            'variable': u'переменный',
            'west'  :   u'З',
            'w'     :   u'З',
            'wnw'   :   u'СЗ',
            'wsw'   :   u'ЮЗ',
        }
        if value in dict_enru_wind_direction:
            value = dict_enru_wind_direction[value]
        return value

    def _convert_condition_en2ru(self, value):
        value = value.lower()
        dict_enru_wind_direction = {
            'sun'           :   u'безобл.',
            'clear sky'     :   u'безобл.',
            'partly cloudy' :   u'перем. обл.',
            'fair'          :   u'ясно',
            'snow'          :   u'снег',
            'cloudy'        :   u'облачно',
            'light rain'    :   u'неб. дождь',
            'light rain showers'    :   u'неб. дождь',
            'heavy rain showers'    :   u'дождь',
            'rain showers'  :   u'ливни',
            'rain showers with thunder' :   u'гроза',
            'sleet showers' :   u'дождь-снег',
            'snow showers'  :   u'мокрый снег',
            'rain'          :   u'дождь',
            'heavy rain'    :   u'дождь',
            'rain and thunder' :   u'гроза',
            'sleet'         :   u'дождь-снег',
            'snow'          :   u'снег',
            'snow and thunder' :   u'снег',
            'fog'           :   u'туман',
            'sleet showers and thunder' : u'снег',
            'snow showers and thunder' :   u'снег',
            'rain and thunder' :   u'гроза',
            'sleet and thunder' :   u'снег',
            'light sleet' :   u'неб. снег',
            'heavy sleet' :   u'мокрый снег',
            'heavy snow' :   u'снег',
            'light sleet showers' :   u'неб. снег',
            'light snow'    : u'неб. снег',
            'light snow showers'    : u'неб. снег',
            'heavy snow showers'    : u'снег',
        }
        if value in dict_enru_wind_direction:
            value = dict_enru_wind_direction[value]
        return value

    def __unicode__(self):
        if self.fact_temperature != '' and self.fact_condition != '' and self.fact_wind_direction != '' and self.fact_wind_speed != '':
            return u'%s° C, %s, %s ветер %s м/с' % (self.fact_temperature, self.fact_condition, self.fact_wind_direction, self.fact_wind_speed)


def main(location):
    weather = yrnoWeather(location)
    print unicode(weather)
    for item in weather.get_weather_by_hour(location):
        print item['pressure']

if __name__ == "__main__":
    sys.exit(main('Russia/Irkutsk/Irkutsk'))
