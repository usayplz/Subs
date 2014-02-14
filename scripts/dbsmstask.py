#!/usr/bin/env python
# -*- coding: utf-8 -*-

import MySQLdb as db
import sys
import logging
import time
import datetime
from bwc_city import BWCCity
from yandex_weather import YandexWeather
from yrno_weather import yrnoWeather

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
            self.cursor.execute('SET TIME_ZONE = "+00:00"')
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
                m.name, w.text
            from 
                sender_weathertext w, sender_mailing m
            where 
                m.id = %(mailing_id)s
                and mailing_id = m.id
                and now() between time_from and time_to
            limit 1
        '''
        try:
            mailing_id = self.get_mailing_id(mobnum)
            if mailing_id:
                (weather, last_date) = self.weather.get(mailing_id, (None, None))
                if weather and last_date and time.time()-self.weather.get(mailing_id, (None, 0))[1] < self.WEATHER_TIMEOUT:
                    return (mailing_id, weather)
                else:
                    self.cursor.execute(sql, { "mailing_id": mailing_id, })
                    row = self.cursor.fetchone()
                    self.connection.commit()
                    if row:
                        name, weather = row
                        # weather = unicode(YandexWeather(location))
                        # weather = unicode(yrnoWeather(yrno_location))
                        if weather:
                            self.weather[mailing_id] = (u'%s: %s' % (name, weather), time.time())
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
                return row[0] if row else None

        except db.Error, e:
            self.raise_error(e)

    def subscribe(self, mobnum, mailing_id):
        sql_select = '''
            select count(*) from sender_subscriber where mobnum = %(mobnum)s and mailing_id = %(mailing_id)s
        '''
        sql_insert = '''
            insert into sender_subscriber
                (mobnum, mailing_id, status, create_date)
            values
                (%(mobnum)s, %(mailing_id)s, 0, NOW())
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
            self.cursor.execute(sql_select, {
                'mobnum': mobnum,
                'mailing_id': mailing_id,
            })
            row = self.cursor.fetchone()
            if row[0] > 0:
                self.cursor.execute(sql_update, {
                    'mobnum': mobnum,
                    'mailing_id': mailing_id,
                })
            else:
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
            limit 30
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

    def get_all_city(self):
        sql = '''
            select
                id, name, bwc_location_code, weather_location_code,create_date, create_user_id, yrno_location_code
            from
                sender_mailing
            order by
                id
        '''
        try:
            self.cursor.execute(sql, {})
            self.connection.commit() # or will be use a cache
        except db.Error, e:
            self.raise_error(e)
            return []

        return self.cursor.fetchall()

    def get_weather_subscribers(self):
        sql = '''
            select
                s.mobnum, w.text, s.id, s.mailing_id, w1.temperature, m.name
            from
                sender_subscriber s, sender_weathertext w, sender_weathertext w1, sender_mailing m
            where 
                s.status = 0 -- подписан
                and m.id = s.mailing_id
                and w.mailing_id = s.mailing_id
                and DATE_ADD(NOW(), INTERVAL 7 HOUR) between w.time_from and w.time_to
                and w1.mailing_id = s.mailing_id
                and DATE_ADD(NOW(), INTERVAL 4 HOUR) between w1.time_from and w1.time_to
        '''
        try:
            self.cursor.execute(sql, { })
            self.connection.commit()
        except db.Error, e:
            self.raise_error(e)
            return []
        return self.cursor.fetchall()

    def get_mailing_list(self):
        sql = '''
            select
                m.yrno_location_code, m.id
            from
                sender_mailing m
            where 
                m.yrno_location_code is not null
        '''
        try:
            self.cursor.execute(sql, {})
            self.connection.commit()
        except db.Error, e:
            self.raise_error(e)
            return []
        return self.cursor.fetchall()

    def clear_weather_texts(self):
        sql = '''
            delete from sender_weathertext where create_date < date_sub(NOW(), interval 7 day)
        '''
        try:
            self.cursor.execute(sql, {})
            self.connection.commit()
        except db.Error, e:
            self.raise_error(e)

    def add_weather_text(self, mailing_id, weather):
        sql = '''
            select count(*) from sender_weathertext where time_from = CONVERT_TZ(%(time_from)s, @@session.time_zone, '-09:00')
        '''
        try:
            self.cursor.execute(sql, { 'time_from': weather['time_from'], })
        except db.Error, e:
            self.raise_error(e)
 
        row = self.cursor.fetchone()
        if int(row[0]) > 0:
            return -1

        sql = '''
            insert into sender_weathertext
                (mailing_id, text, temperature, wcondition, wind_direction, wind_speed, time_from, time_to, create_date, pressure)
            values
                (%(mailing_id)s, %(text)s, %(temperature)s, %(condition)s, %(wind_direction)s, %(wind_speed)s, CONVERT_TZ(%(time_from)s, @@session.time_zone, '-09:00'), CONVERT_TZ(%(time_to)s, @@session.time_zone, '-09:00'), NOW(), %(pressure)s)
        '''
        try:
            self.cursor.execute(sql, {
                'mailing_id': mailing_id,
                'text': weather['text'],
                'temperature': weather['temperature'],
                'condition': weather['condition'],
                'wind_direction': weather['wind_direction'],
                'wind_speed': weather['wind_speed'],
                'time_from': weather['time_from'],
                'time_to': weather['time_to'],
                'pressure': weather['pressure'],
            })
            self.connection.commit()
        except db.Error, e:
            self.raise_error(e)
            return -1
        return self.cursor.lastrowid


def main(args=None):
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    db_config = {'host': 'localhost', 'user': 'subs', 'passwd': 'njH(*DHWH2)', 'db': 'subsdb'}
    tasker = dbSMSTask(db_config, logger)

    tasker.clear_weather_texts()
    mailings = tasker.get_mailing_list()
    weather = yrnoWeather()
    for mailing in mailings:
        yrno_location, mailing_id = mailing
        for i, item in enumerate(weather.get_weather_by_hour(yrno_location)):
            tuple_time = time.strptime(item['time_from'].replace("-", ""), "%Y%m%dT%H:%M:%S")
            item['time_from'] = datetime.datetime(*tuple_time[:6])
            tuple_time = time.strptime(item['time_to'].replace("-", ""), "%Y%m%dT%H:%M:%S")
            item['time_to'] = datetime.datetime(*tuple_time[:6])
            item['text'] = u'%s° C, %s, %s ветер %s м/с' % (item['temperature'], item['condition'], item['wind_direction'], item['wind_speed'])
            tasker.add_weather_text(mailing_id, item)


def subs():
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    db_config = {'host': 'localhost', 'user': 'subs', 'passwd': 'njH(*DHWH2)', 'db': 'subsdb'}
    tasker = dbSMSTask(db_config, logger)

    # создаем рассылку
    subscribers = tasker.get_weather_subscribers()
    for subscriber in subscribers:
        mobnum, weather, sid, mailing_id, temperature, name = subscriber
        text = u'%s: %s' % (name, weather.replace(u"°", u" "+temperature+u"°"))
        tasker.add_new_task(mobnum, 'subs', text, 0)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        subs()
    else:
        main()
