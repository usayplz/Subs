#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3 as db
import logging, time
from datetime import datetime

class dbSMSTask(object):
    connection = None
    connection_state = 0
    cursor = None
    weather = None
    weather_time = 0
    weather_timeout = 15*60

    def __init__(self, connection_string):
        self.connection_state = 0
        self.connect(connection_string)

    def __del__(self):
        self.connection.commit()
        self.connection.close()

    def connect(self, connection_string):
        try:
            self.connection = db.connect(connection_string)
            self.cursor = self.connection.cursor()
            self.connection_state = 1
        except db.Error, e:
            self.connection_state = 0
            print e

    def set_weather(self):
        sql = '''
            select sms_text, from_date from sender_smstext order by from_date desc limit 1
        '''
        try:
            self.cursor.execute(sql, {})
            results = self.cursor.fetchall()
            if results:
                self.weather = results[0][0]
            else:
                self.weather = ''
        except db.Error, e:
            self.connection_state = 0
            print e
           
    
    def add_new_task(self, mobnum, message_id):
        status = 0
        if not self.weather or time.time()-self.weather_time > self.weather_timeout:
            self.set_weather()
            self.weather_time = time.time()

        sql = '''
            insert into sender_smstask 
                (mobnum, sms_text, delivery_date, status, message_id)
            values 
                (:mobnum, :sms_text, :delivery_date, :status, :message_id)
        '''
        try:
            self.cursor.execute(sql, {
                "mobnum": mobnum,
                "sms_text": self.weather,
                "delivery_date": str(datetime.utcnow()),
                "status": status,
                "message_id": message_id,
            })
            self.connection.commit()
        except db.Error, e:
            self.connection_state = 0
            print e

    def update_task_status(self, status, message_id):
        sql = '''
            update sender_smstask
            set status = :status
            where message_id = :message_id
        '''
        try:
            self.cursor.execute(sql, { 
                "status": status,
                "mailing_id": mailing_id,
            })
            self.connection.commit()
        except db.Error, e:
            self.connection_state = 0
            print e


def main(args=None):
    tasker = dbSMSTask('../local.db')
    tasker.add_new_task('9021702030', 123456)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()
