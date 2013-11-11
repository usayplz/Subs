#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
import urllib


class BWCCity():
    URL = 'https://sasgwapi.bwc.ru/cgi-bin/geotarget.cgi'
    PASSPHRASE = 'mrkt27Yps'

    def __init__(self, mobnum):
        query_id = put_bwc_geotarget(mobnum)
        bwc_code_id = get_bwc_geotarget(query_id)
        return bwc_code_id

    def put_bwc_geotarget(self, mobnum):
        params = urllib.urlencode({'action': 'put', 'passphrase': PASSPHRASE, 'mob_num': mobnum })
        request = urllib2.Request(URL, params, headers)
        response = urllib2.urlopen(request)
        return response.read().decode('utf-8')

    def get_bwc_geotarget(self, query_id):
        params = urllib.urlencode({'action': 'get', 'passphrase': PASSPHRASE, 'query_id': query_id })
        request = urllib2.Request(URL, params, headers)
        response = urllib2.urlopen(request)
        return response.read().decode('utf-8')

if __name__ == '__main__':
    print BWCCity('9500500600')
