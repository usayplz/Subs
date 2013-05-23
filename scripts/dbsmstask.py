#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3 as db

class dbSMSTask(object):
    connection = None
    connection_state = 0
    cursor = None
    weather = None
    weather_time = None
    weather_timeout = 15*60

    def __init__(self, connection_string):
        self.connection_state = 0
        return connect(connection_string)
            
    def connect(self):
        try:
            self.connection = db.connect(connection_string)
            self.cursor = connection.cursor()
            self.connection_state = 1
        except db.Error, e:
            self.connection_state = 0
            return e
        return True

    def get_weather(self):
        sql = '''
            select sms_test, time from sms_text order by from_time desc limit 1
        '''
        try:
            self.cursor.execute(sql, {})
        except db.Error, e:
            self.connection_state = 0
            return e
        weather, self.weather_time = self.cursor.fetchone()
        return weather
    
    def __del__(self):
        self.connection.commit()
        self.connection.close()

    def add_new_task(self, mobnum, message_id):
        status = 0
        if not self.weather or time.now()-self.weather_time > self.weather_timeout:
            self.weather = self.get_weather()

        sql = '''
            insert into sender_smstask 
                (mobnum, sms_text, status, message_id)
            values 
                (:mobnum, :sms_text, :status, :message_id)
        '''
        try:
            self.cursor.execute(sql, {
                "mobnum": mobnum,
                "sms_text": self.weather,
                "status": status, 
                "message_id": message_id
            })
            self.connection.commit()
        except db.Error, e:
            self.connection_state = 0
            return e
        return True

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
            return e
        return True


def main(args):
    tasker = dbSMSTask('../local.db')
    tasker.add_new_task('9021702030', 123456)

if __name__ == '__main__':
    main()
