#!/usr/bin/env python
# -*- coding: utf-8 -*-

import MySQLdb as db
import logging, time
from datetime import datetime
from wunderground import WundergroundWather

class dbSMSTask(object):
    WEATHER_TIMEOUT = 15*60
    MAILING = 1
    KEY = 'b5720198c3228276'
    LOCATION = 'Irkutsk'

    def __init__(self, db_config):
        self.db_config = db_config
        self.connection_state = 0
        self.connect()

        self.weather = ''
        self.connection_state = 0
        self.weather_timer = 0

    def __del__(self):
        self.connection.commit()
        self.connection.close()

    def connect(self):
        try:
            self.connection = db.connect(
                host=self.db_config.get('host'),
                user=self.db_config.get('user'), 
                passwd=self.db_config.get('passwd'), 
                db=self.db_config.get('db'), 
                charset='utf8',
            )
            self.cursor = self.connection.cursor()
            self.cursor.execute('SET SESSION query_cache_type = OFF')
            self.connection_state = 1
        except db.Error, e:
            self.connection_state = 0
            print e

    def add_new_task(self, mobnum, in_text):
        status = 1
        if not self.weather or time.time()-self.weather_timer > self.WEATHER_TIMEOUT:
            self.weather = unicode(WundergroundWather(self.KEY, self.LOCATION))
            self.weather_timer = time.time()
            self.add_weather()

        sql = '''
            insert into sender_smstask
                (mobnum, in_text, out_text, delivery_date, status)
            values
                (%(mobnum)s, %(in_text)s, %(out_text)s, %(delivery_date)s, %(status)s)
        '''
        try:
            self.cursor.execute(sql, {
                'mobnum': mobnum,
                'in_text': in_text,
                'out_text': self.weather,
                'delivery_date': datetime.utcnow(),
                'status': status,
            })
            self.connection.commit()
        except db.Error, e:
            self.connection_state = 0
            print e
            return -1
        return self.cursor.lastrowid

    def update_task(self, status, task_id='', message_id='', new_message_id=''):
        sql = '''
            update sender_smstask
            set status = %(status)s,
                message_id = %(new_message_id)s,
                sent_date = NOW()
            where message_id = %(message_id)s or id = %(task_id)s
        '''
        try:
            self.cursor.execute(sql, { 
                "status": status,
                "message_id": message_id,
                "task_id": task_id,
                "new_message_id": new_message_id,
            })
            self.connection.commit()
        except db.Error, e:
            self.connection_state = 0
            print e

    def add_weather(self):
        sql = '''
            insert into sender_smstext 
                (sms_text, mailing_id, from_date) 
            values 
                (%(sms_text)s, %(mailing_id)s, %(from_date)s)
        '''
        try:
            self.cursor.execute(sql, { 
                'sms_text': self.weather,
                'mailing_id': self.MAILING, 
                'from_date': datetime.utcnow(), 
            })
            self.connection.commit()
        except db.Error, e:
            self.connection_state = 0
            print e

    def check_tasks(self):
        sql = '''
            select
                id, mobnum, out_text
            from 
                sender_smstask
            where
                status = 0
                and delivery_date <= NOW()
        '''
        try:
            self.cursor.execute(sql, {})
            self.connection.commit() # or will be use a cache
        except db.Error, e:
            self.connection_state = 0
            print e
            return []

        return self.cursor.fetchall()

def main(args=None):
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    db_config = {'host': 'localhost', 'user': 'subs', 'passwd': 'njH(*DHWH2)', 'db': 'subsdb'}
    tasker = dbSMSTask(db_config)
    tasker.add_new_task('9021702030', 123456)

if __name__ == '__main__':
    main()
