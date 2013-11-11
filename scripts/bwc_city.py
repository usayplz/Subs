#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
import urllib
import re
import time


class BWCCity():
    URL = 'https://sasgwapi.bwc.ru/cgi-bin/geotarget.cgi'
    PASSPHRASE = 'mrkt27Yps'
    TIMEOUT = 10
    bwc_code_id = u''

    def __init__(self, mobnum):
        query_id = self.put_bwc_geotarget(mobnum)
        timer = time.time()
        bwc_str = u''
        while ('city_id' not in bwc_str or time.time()-timer > self.TIMEOUT):
            bwc_str = self.get_bwc_geotarget(query_id)
        self.bwc_code_id = re.findall(r'city_id=(\d+)', bwc_str)

    def __str__(self):
        if self.bwc_code_id:
            return self.bwc_code_id[0]
        else:
            return ''

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
    print BWCCity('79500500600')
