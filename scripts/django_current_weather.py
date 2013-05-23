#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wunderground import WundergroundWather
import sqlite3 as db
import sys
from datetime import datetime


def insert_weather(weather, mailing_id):
    sql = '''
        insert into sender_smstext 
            (sms_text, mailing_id, from_date, to_date) 
        values 
            (:sms_text, :mailing_id, :from_date, :to_date)
    '''
    try:
        connection = db.connect('../local.db')
        cursor = connection.cursor()
        cursor.execute(sql, { 
            "sms_text": weather,
            "mailing_id": mailing_id, 
            "from_date": '2013-05-20 03:04:05', 
            "to_date": '2013-05-21 03:04:05'
        })
        connection.commit()
        connection.close()
    except db.Error, e:
        print e
        return 2


def main(argv=None):
    mailing_id = 1
    key = "b5720198c3228276"
    location = "Irkutsk"
    weather = WundergroundWather(key, location)
    return insert_weather(unicode(weather), mailing_id)

if __name__ == "__main__":
    sys.exit(main())