#!/usr/bin/python
# -*- coding: utf-8 -*-

import re, codecs, string
import MySQLdb as db


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


def update(code, bwc_location_code):
    sql = '''
        update sender_mailing
        set weather_location_code = %(code)s
        where bwc_location_code = %(bwc_location_code)s
    '''
    try:
        cursor.execute(sql, {
            'bwc_location_code': bwc_location_code,
            'code': code,
        })
        connection.commit()
    except db.Error, e:
        connection_state = 0
        return -1

filename = 'cities.xml'
sql = '''
    select
        name, bwc_location_code
    from
        sender_mailing
'''
cursor.execute(sql, {})
for item in cursor.fetchall():
    name, bwc_location_code = item
    print name, bwc_location_code
    find = unicode('>'+name+'<')+u''
    f = codecs.open(filename, "r", 'utf-8')
    for line in f:
        line = line.strip()
        if find in line:
            line = line[10:]
            line = line[:string.find(line, '"')]
            # print line
            update(line, bwc_location_code)

exit()

f = codecs.open(filename, "r", 'utf-8')
for line in f:
    line = line.strip()
    m = re.match(ur'(\w+),(("[А-Яа-я ,-\.]+\s([А-Яа-я-ё]+)")|("[А-Яа-я ,-\.]+\.([А-Яа-я-ё]+)")|([А-Яа-я-ё]+)),', line, re.U)
    if m:
        if m.groups()[3] is None:
            point = m.groups()[1].encode('utf-8')
        else:
            point = m.groups()[3].encode('utf-8')
        print m.groups()[0].encode('utf-8'), point
