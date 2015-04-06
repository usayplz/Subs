#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
import urllib
import re
import time
import sys

import MySQLdb as db
sys.path.append('/var/www/subs/')
from local_settings import DATABASES
db_config = DATABASES['default']

class BWCCity():
    URL = 'https://sasgwapi.bwc.ru/cgi-bin/geotarget.cgi'
    PASSPHRASE = 'mrkt27Yps'
    TIMEOUT = 10
    bwc_code_id = u''

    def __init__(self, mobnum):
        self.bwc_code_id = self.get_city_data(mobnum)
        if self.bwc_code_id and not self.bwc_code_id[0]:
            query_id = self.put_bwc_geotarget(mobnum)
            timer = time.time()
            bwc_str = u''
            while ('city_id' not in bwc_str and time.time()-timer < self.TIMEOUT):
                bwc_str = self.get_bwc_geotarget(query_id)
            self.bwc_code_id = re.findall(r'city_id=(\d+)', bwc_str)

    def __str__(self):
        if self.bwc_code_id:
            return self.bwc_code_id[0]
        else:
            return ''

    def get_city_data(self, mobnum):
        cursor = None
        connection = None
        try:
            connection = db.connect(
                host=db_config.get('HOST'),
                user=db_config.get('USER'), 
                passwd=db_config.get('PASSWORD'), 
                db=db_config.get('NAME'), 
                charset='utf8',
            )

            cursor = connection.cursor()
            cursor.execute('SET SESSION query_cache_type = OFF')
            cursor.execute('SET TIME_ZONE = "+00:00"')
            cursor.execute('SET lc_time_names = "ru_RU"')
        except db.Error, e:
            raise_error(e)

        sql = '''
            select bwc_location_code from sender_data where name = %(mobnum)s limit 1
        '''
        cursor.execute(sql, { "mobnum": mobnum })
        row = cursor.fetchone()
        connection.commit()
        connection.close()
        return row

    def put_bwc_geotarget(self, mobnum):
        params = urllib.urlencode({'action': 'put', 'passphrase': self.PASSPHRASE, 'mob_num': mobnum })
        request = urllib2.Request(self.URL, params)
        response = urllib2.urlopen(request)
        return response.read()

    def get_bwc_geotarget(self, query_id):
        params = urllib.urlencode({'action': 'get', 'passphrase': self.PASSPHRASE, 'query_id': query_id })
        request = urllib2.Request(self.URL, params)
        response = urllib2.urlopen(request)
        return response.read()

if __name__ == '__main__':
    # print BWCCity('79500500600')
    #print BWCCity('79500500171')
    print BWCCity('79086493755')
