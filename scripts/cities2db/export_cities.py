#!/usr/bin/python
# -*- coding: utf-8 -*-

import re, codecs
import MySQLdb as db

p = u'1025.6'
p = float(p)/1.333
print p
exit()

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


def insert(code, name):
    sql = '''
        insert into sender_mailing
            (name, bwc_location_code, create_date)
        values
            (%(name)s, %(code)s, NOW())
    '''
    try:
        cursor.execute(sql, {
            'name': name,
            'code': code,
        })
        connection.commit()
    except db.Error, e:
        connection_state = 0
        return -1

filename = 'list_cities.csv'
filename = 'rass.txt'
f = codecs.open(filename, "r", 'utf-8')
pre_point = u''
for line in f:
    line = line.rstrip()
    if len(line) > 9:
        print line
        cursor.execute("update sender_smstask set status=0 where mobnum = %(phone)s and in_text = 'subs'  and delivery_date > date_sub(NOW(), interval 1 day)", {'phone': line})
        connection.commit()
#    line = line.strip()
#    m = re.match(ur'(\w+),(("[А-Яа-я ,-\.]+\s([А-Яа-я-ё]+)")|("[А-Яа-я ,-\.]+\.([А-Яа-я-ё]+)")|([А-Яа-я-ё]+)),', line, re.U)
#    if m:
#        if m.groups()[3] is None:
#            point = m.groups()[1].encode('utf-8')
#        else:
#            point = m.groups()[3].encode('utf-8')
#        print m.groups()[0].encode('utf-8'), point
#        if pre_point != point:
#            insert(m.groups()[0].encode('utf-8'), point)
#        pre_point = point
