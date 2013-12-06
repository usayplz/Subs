#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, urllib, math
from xml.etree import ElementTree


class yrnoWeather():
    def __init__(self, location):
        self.weather_url = 'http://www.yr.no/place/%s/forecast.xml' % (location)
        self.fact_temperature = ''
        self.fact_condition = ''
        self.fact_wind_direction = ''
        self.fact_wind_speed = ''

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
                self.fact_wind_direction = self._convert_wind_en2ru(time[2].get('code'))
                self.fact_wind_speed = int(float(time[3].get('mps')))
                break
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

    def _convert_condition_en2ru(self, value):
        value = value.lower()
        dict_enru_wind_direction = {
            'sun/clear sky' :   u'солнечно',
            'partly cloudy' :   u'переменная облачность',
            'fair'          :   u'ясно',
            'snow'          :   u'снег',
            'cloudy'        :   u'облачно',
            'rain showers'  :   u'ливни',
            'rain showers with thunder' :   u'дождь с грозой',
            'sleet showers' :   u'сильные дожди со снегом',
            'snow showers'  :   u'мокрый снег',
            'rain'          :   u'дождь',
            'heavy rain'    :   u'сильный дождь',
            'rain and thunder' :   u'дождь и гроза',
            'sleet'         :   u'дождь со снегом',
            'snow'          :   u'снег',
            'snow and thunder' :   u'снег и гроза',
            'fog'           :   u'туман',
            'sleet showers and thunder' : u'сильные дожди со снегом и грозой',
            'snow showers and thunder' :   u'мокрый снег и гроза',
            'rain and thunder' :   u'дождь и гроза',
            'sleet and thunder' :   u'мокрый снег и гроза',
        }
        if value in dict_enru_wind_direction:
            value = dict_enru_wind_direction[value]
        return value

    def __unicode__(self):
        return u'%s° C, %s, %s ветер %s м/с' % (self.fact_temperature, self.fact_condition, self.fact_wind_direction, self.fact_wind_speed)


def main(location):
    weather = yrnoWeather(location)
    print unicode(weather)

if __name__ == "__main__":
    sys.exit(main('Russia/Irkutsk/Irkutsk'))
