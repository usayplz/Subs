#!/usr/bin/python
# -*- coding: utf-8 -*-

import re, codecs, string
import MySQLdb as db
import urllib2
import time


db_config = {'host': 'localhost', 'user': 'subs', 'passwd': 'njH(*DHWH2)', 'db': 'subsdb'}
connection = db.connect(
    host=db_config.get('host'),
    user=db_config.get('user'),
    passwd=db_config.get('passwd'),
    db=db_config.get('db'),
    charset='utf8',
)
cursor = connection.cursor()
cursor.execute('SET SESSION query_cache_type = OFF')


def update(id, code):
    sql = '''
        update sender_mailing
        set yrno_location_code = %(code)s
        where id = %(id)s
    '''
    try:
        cursor.execute(sql, {
            'id': id,
            'code': code,
        })
        connection.commit()
    except db.Error, e:
        return -1

# f = codecs.open('1.txt', "r", 'utf-8')
# for line in f:
#     line = line.strip()
#     if u'/place/Russia/' in line:
#         code = re.findall(r'/place/Russia/([a-zA-Z0-9~\-_/]+)"', line)
#         print code
#         # print line
#         break
#     if u'/sted/Russland/' in line:
#         code = re.findall(r'/sted/Russland/([a-zA-Z0-9~\-_/]+)"', line)
#         print code
#         break
# exit()


yr_search_url = u'http://www.yr.no/soek/soek.aspx?sted=%s'
sql = '''
    select
        id, name, bwc_location_code
    from
        sender_mailing
    where
        yrno_location_code is null
    order by
        name
'''
cursor.execute(sql, {})
for row in cursor.fetchall():
    id, name, bwc_location_code = row
    name = name.replace(u' ', u'+')
    print name.encode('utf-8')
    search = yr_search_url % name
    response = urllib2.urlopen(search.encode('utf-8'))
    html = response.read()
    response.close()
    code = re.findall(r'/place/Russia/([a-zA-Z0-9~\-_\'\`/]+)"', html)
    if not code:
        code = re.findall(r'/sted/Russland/([a-zA-Z0-9~\-_\'\`/]+)"', html)
    print code
    if code:
        update(id, u'Russia/%s' % code[0])
    else:
        update(id, u'---')
    time.sleep(10)

exit()
