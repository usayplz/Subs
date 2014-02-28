#!/usr/bin/python
# -*- coding: utf-8 -*-

import re, codecs
import MySQLdb as db

import datetime
subs_time = '17:00:00'
h = int(subs_time[0:2])
h_now = int(str(datetime.datetime.now())[11:13])
if h_now < h:
    print h_now, h
else:
    print "false"
#exit()
print int("%s%s" % (subs_time[0:2], subs_time[3:5]))
exit()

s = u'*8181*1000#'
s = u'*818*1234#'
s = u'*8181*1300#'
s = u'*818*1#'
#s = u'*8181*1000#'
s = re.sub("^(\*8181|\*818)", "", s)
s = re.sub("[^\d]", "", s)
try:
    if len(s) == 4:
        h = int(s[0:2])
        m = int(s[2:4])
    elif len(s) == 3:
        h = int(s[0:1])
        m = int(s[1:3])
    elif len(s) == 3:
        h = int(s[0:1])
        m = int(s[1:3])
    elif len(s) == 2:
        h = int(s[0:2])
        m = 0
    elif len(s) == 1:
        h = int(s[0:1])
        m = 0
    else:
        h = None
        m = None
except:
    h = None
    m = None
    print "false None"

subs_time = ""
if (h >= 0 and h < 24 and m >= 0 and m < 60):
    subs_time = "%s:%s:00" % (str(h).zfill(2), str(m).zfill(2))
else:
    print "false", subs_time

print s, h, m, subs_time
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

sql = '''
    update
        sender_subscriber
    set
        subs_time = %(subs_time)s
    where
        mobnum = '79021702030'
'''
try:
    cursor.execute(sql, {
        'subs_time': subs_time,
    })
    connection.commit()
except db.Error, e:
    print "false DB"

exit()

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
