#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wunderground import WundergroundWather
import sqlite3 as db
import sys
from datetime import datetime


def main(argv=None):
    key = "b5720198c3228276"
    location = "Irkutsk"
    weather = WundergroundWather(key, location)

    sql = '''
        insert into sender_smstext 
            (sms_text, mailing_id, from_date, to_date) 
        values 
            (:sms_text, :mailing_id, :from_date, :to_date)
    '''
    mailing = 1
    try:
        connection = db.connect('../local.db')
        cursor = connection.cursor()
        cursor.execute(sql, { 
            "sms_text": unicode(weather), 
            "mailing_id": mailing, 
            "from_date": '2013-05-20 03:04:05', 
            "to_date": '2013-05-21 03:04:05'
        })
        connection.commit()
        connection.close()
    except db.Error, e:
        print e
        return 2


if __name__ == "__main__":
    sys.exit(main())
