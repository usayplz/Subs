#!/usr/bin/env python
# -*- coding: utf-8 -*-

import MySQLdb as db
import logging, time
from yandex_weather import YandexWeather

class dbSMSTask(object):

    def __init__(self, db_config, logger):
        self.db_config = db_config
        self.logger = logger
        self.connection_state = 0
        self.connect()

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
            raise_error(e)

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
            raise_error(e)
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
            raise_error(e)

    def get_current_weather(self, mobnum):
        return (3, u'Александровск')
        # sms_text = ''
        # sql = '''
        #     select 
        #         location, sms_text 
        #     from 
        #         sender_mailing m LEFT OUTER JOIN sender_smstext s
        #         on s.code = m.code and NOW() between from_date and to_date
        #     where
        #         m.code = %(mailing_id)s
        # '''
        # try:
        #     self.cursor.execute(sql, {'mailing_id': mailing_id,})
        #     sms_text, location = self.cursor.fetchone()
        #     self.connection.commit()
        #     if sms_text == '' and location != '':
        #         sms_text = unicode(YandexWeather(location))
        # except db.Error, e:
        #     raise_error(e)
        # return sms_text

    # def load_today_weather(self):
    #     sql = '''
    #         select 
    #             code, location
    #         from 
    #             sender_mailing
    #     '''
    #     sql_insert = '''
    #         insert into sender_smstext 
    #             (sms_text, mailing_id, from_date, to_date)
    #         values 
    #             (%(sms_text)s, %(mailing_id)s, convert_tz(STR_TO_DATE(%(from_date)s, '%%Y-%%m-%%d %%T'), '+09:00', '+00:00'), convert_tz(STR_TO_DATE(%(to_date)s, '%%Y-%%m-%%d %%T'), '+09:00', '+00:00'))
    #     '''
    #     try:
    #         self.cursor.execute(sql, {})
    #         for item in self.cursor.fetchall():
    #             mailing_id, location = item

    #             weather = YandexWeather(location)
    #             for w in weather.get_weather_by_hour():
    #                 from_date = u'%s %s:00:00' % (w['date'], w['hour_at'].zfill(2))
    #                 to_date = u'%s %s:59:59' % (w['date'], w['hour_at'].zfill(2))
    #                 weather_hour_at = u'%s: %s° C, %s, %s ветер %s м/с' % (w['city'], w['temperature'], w['condition'], w['wind_direction'], w['wind_speed'])
    #                 # print "DEBUG: ", from_date, to_date, weather_hour_at
    #                 self.cursor.execute(sql_insert, {
    #                     'sms_text': weather_hour_at,
    #                     'mailing_id': mailing_id, 
    #                     'from_date': from_date,
    #                     'to_date': to_date,
    #                 })

    #             self.connection.commit()
    #             time.sleep(3)
    #     except db.Error, e:
    #         self.connection_state = 0
    #         self.logger.critical(e)
    #         raise
    #         return -1
    #     return 1

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
                status = 1
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
            raise_error(e)
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
            raise_error(e)
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
            raise_error(e)
            return []

        return self.cursor.fetchall()

    def raise_error(error):
        self.connection_state = 0
        self.logger.critical(e)
        raise


def main(args=None):
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    db_config = {'host': 'localhost', 'user': 'subs', 'passwd': 'njH(*DHWH2)', 'db': 'subsdb'}
    tasker = dbSMSTask(db_config, logger)
    # tasker.load_today_weather()

if __name__ == '__main__':
    main()
