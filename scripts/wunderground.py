#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""get_weather.py
Returns current conditions, forecast and alerts from wunderground.com.
"""

import sys, urllib
from xml.etree import ElementTree as ET


class WundergroundWather():
    """get weather from wunderground.com"""

    def __init__(self, key, location):
        try:
            proxies = {'http': 'http://proxy.bwc.ru:3128'}
            current_conditions = 'http://api.wunderground.com/api/%s/conditions/lang:RU/q/Russia/%s.xml' % (key, location)
            urllib.socket.setdefaulttimeout(8)
            usock = urllib.urlopen(current_conditions, proxies=proxies)
            tree = ET.parse(usock)
            usock.close()
        except:
            print 'ERROR - Current Conditions - Could not get information from server...'
            sys.exit(2)

        for current_observation in tree.findall("current_observation"):
            self.city = current_observation.find('display_location/city').text
            self.temperature = current_observation.find('temp_c').text
            self.weather = current_observation.find('weather').text
            self.wind_direction = current_observation.find('wind_dir').text
            self.wind_speed = current_observation.find('wind_kph').text

        self.wind_direction = self._convert_wind_en2ru(self.wind_direction)
        self.wind_speed = self._kph2mps(self.wind_speed)
    
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

    def __unicode__(self):
        weather = u'%s: %s° C, %s, %s ветер %s м/с' % (self.city, self.temperature, self.weather, self.wind_direction, self.wind_speed)
        return weather


def main(key, location):
    weather = WundergroundWather(key, location)
    print unicode(weather)

if __name__ == "__main__":
    key = "b5720198c3228276"
    location = "Irkutsk"
    sys.exit(main(key, location))
