#!/usr/bin/env python
# -*- coding: utf-8 -*-

import MySQLdb as db
import logging
import time
from bwc_city import BWCCity
from yandex_weather import YandexWeather


class dbSMSTask(object):
    WEATHER_TIMEOUT = 30*60     # 30 min

    def __init__(self, db_config, logger):
        self.db_config = db_config
        self.logger = logger
        self.connection_state = 0
        self.connect()
        self.weather = {}

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
            # self.cursor.execute('SET TIME_ZONE = "+00:00"')
            self.connection_state = 1
        except db.Error, e:
            self.raise_error(e)

    def add_new_task(self, mobnum, in_text, out_text, status):
        sql = '''
            insert into sender_smstask
                (mobnum, in_text, out_text, delivery_date, status)
            values
                (%(mobnum)s, %(in_text)s, %(out_text)s, NOW(), %(status)s)
        '''
        try:
            self.cursor.execute(sql, {
                'mobnum': mobnum,
                'in_text': in_text,
                'out_text': out_text,
                'status': status,
            })
            self.connection.commit()
        except db.Error, e:
            self.raise_error(e)
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
            self.raise_error(e)

    def get_current_weather(self, mobnum):
        sql = '''
            select
                weather_location_code, name
            from
                sender_mailing
            where
                id = %(mailing_id)s
        '''
        try:
            mailing_id = self.get_mailing_id(mobnum)
            if mailing_id:
                (weather, last_date) = self.weather.get(mailing_id, (None, None))
                if weather and last_date and time.time()-self.weather_timer < self.WEATHER_TIMEOUT:
                    return (mailing_id, weather)
                else:
                    self.cursor.execute(sql, { "mailing_id": mailing_id, })
                    row = self.cursor.fetchone()
                    self.connection.commit()
                    if row:
                        location, name = row
                        weather = unicode(YandexWeather(location))
                        if weather:
                            self.weather[mailing_id] = (weather, time.time())
                    return mailing_id, self.weather.get(mailing_id, (None, None))[0]
            else:
                return (None, None)
            self.connection.commit()
        except db.Error, e:
            self.raise_error(e)

    def get_mailing_id(self, mobnum):
        sql_mailing_id = '''
            select
                mailing_id, status
            from
                sender_subscriber
            where
                mobnum = %(mobnum)s
            order by
                create_date desc
            limit 1
        '''
        sql_bwc_code = '''
            select
                id, name
            from
                sender_mailing
            where
                bwc_location_code = %(bwc_location_code)s
        '''
        try:
            self.cursor.execute(sql_mailing_id, { "mobnum": mobnum, })
            row = self.cursor.fetchone()
            self.connection.commit()
            if row:
                return row[0]
            else:
                bwc_location_code = BWCCity(mobnum)
                self.cursor.execute(sql_bwc_code, { "bwc_location_code": bwc_location_code, })
                row = self.cursor.fetchone()
                self.connection.commit()
                return row[0]
        except db.Error, e:
            self.raise_error(e)

    def subscribe(self, mobnum, mailing_id):
        sql_insert = '''
            insert into sender_subscriber
                (mobnum, mailing_id, status, create_date)
            values
                (%(mobnum)s, %(mailing_id)s, 1, NOW())
        '''
        sql_update = '''
            update
                sender_subscriber
            set
                status = 0
            where
                mobnum = %(mobnum)s
                and mailing_id = %(mailing_id)s
        '''
        try:
            self.cursor.execute(sql_update, {
                'mobnum': mobnum,
                'mailing_id': mailing_id,
            })
            if self.cursor.rowcount == 0:
                self.cursor.execute(sql_insert, {
                    'mobnum': mobnum,
                    'mailing_id': mailing_id,
                })
            self.connection.commit()
        except db.Error, e:
            self.raise_error(e)
            return 0
        return 1

    def unsubscribe(self, mobnum):
        """
            unsubscriber from all subs
        """
        sql = '''
            update
                sender_subscriber
            set
                status = 1
            where
                mobnum = %(mobnum)s
        '''
        try:
            self.cursor.execute(sql, {'mobnum': mobnum,})
            self.connection.commit()
        except db.Error, e:
            self.raise_error(e)
            return 0
        return 1

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
            self.raise_error(e)
            return []

        return self.cursor.fetchall()

    def raise_error(self, error):
        self.connection_state = 0
        self.logger.critical(error)
        raise


def main(args=None):
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    db_config = {'host': 'localhost', 'user': 'subs', 'passwd': 'njH(*DHWH2)', 'db': 'subsdb'}
    tasker = dbSMSTask(db_config, logger)
    print tasker.get_current_weather('79021702030')
    # tasker.load_today_weather()

if __name__ == '__main__':
    main()
