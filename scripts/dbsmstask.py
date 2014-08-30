#!/usr/bin/env python
# -*- coding: utf-8 -*-

import MySQLdb as db
import sys, re
import logging
import time
import datetime
from bwc_city import BWCCity
from yandex_weather import YandexWeather
from yrno_weather import yrnoWeather
from mail import send_mail

# db config
sys.path.append('/var/www/subs/')
from local_settings import DATABASES
db_config = DATABASES['default']

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
                host=db_config.get('HOST'),
                user=db_config.get('USER'), 
                passwd=db_config.get('PASSWORD'), 
                db=db_config.get('NAME'), 
                charset='utf8',
            )

            self.cursor = self.connection.cursor()
            self.cursor.execute('SET SESSION query_cache_type = OFF')
            self.cursor.execute('SET TIME_ZONE = "+00:00"')
            self.cursor.execute('SET lc_time_names = "ru_RU"')
            self.connection_state = 1
        except db.Error, e:
            self.raise_error(e)

    def add_new_task(self, mobnum, in_text, out_text, status, delivery_date=None):
        if not out_text:
            return -1

        sql = '''
            insert into sender_smstask
                (mobnum, in_text, out_text, delivery_date, status)
            values
                (%(mobnum)s, %(in_text)s, %(out_text)s, ifnull(CONVERT_TZ(%(delivery_date)s, @@session.time_zone, '-09:00'), NOW()), %(status)s)
        '''
        try:
            self.cursor.execute(sql, {
                'mobnum': mobnum,
                'in_text': in_text,
                'out_text': out_text,
                'status': status,
                'delivery_date': delivery_date,
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

    def _parse_time_from_message(self, short_message):
        subs_time = re.sub("^(\*8181|\*818)", "", short_message)
        subs_time = re.sub("[^\d]", "", subs_time)
        h = None
        m = 0
        try:
            if len(subs_time) == 4:
                h = int(subs_time[0:2])
                m = int(subs_time[2:4])
            elif len(subs_time) == 3:
                h = int(subs_time[0:1])
                m = int(subs_time[1:3])
            elif len(subs_time) == 2:
                h = int(subs_time[0:2])
            elif len(subs_time) == 1:
                h = int(subs_time[0:1])
            else:
                return ''
        except:
            return ''

        if (h >= 0 and h < 24 and m >= 0 and m < 60):
            return "%s:%s:00" % (str(h).zfill(2), str(m).zfill(2))
        else:
            return ''

    def set_time(self, mobnum, short_message, mailing_id):
        subs_time = self._parse_time_from_message(short_message)
        if subs_time == '':
            return ''

        sql = '''
            update
                sender_subscriber
            set
                subs_time = %(subs_time)s
            where
                mobnum = %(mobnum)s
        '''
        try:
            self.cursor.execute(sql, {
                'subs_time': subs_time,
                'mobnum': mobnum,
            })
            self.clear_future_task(mobnum)
            self.connection.commit()
        except db.Error, e:
            self.raise_error(e)
            return ''

        # если сегодня еще не рассылали
        h = int("%s%s" % (subs_time[0:2], subs_time[3:5]))
        h_now = int("%s%s" % (str(datetime.datetime.now())[11:13], str(datetime.datetime.now())[14:16]))
        if h_now < h:
            text = u''
            if h > 1600:
                text = self.get_evening_weather(mailing_id)
            else:
                text = self.get_today_weather(mailing_id)
            send_date = "%s %s" % (str(datetime.datetime.now())[0:10], subs_time)
            self.add_new_task(mobnum, 'subs', text, 0, send_date)

        return subs_time

    def clear_future_task(self, mobnum):
        sql = '''
            delete from 
                sender_smstask
            where 
                mobnum = %(mobnum)s
                and delivery_date > NOW()-interval 1 day
        '''
        try:
            self.cursor.execute(sql, {
                'mobnum': mobnum,
            })
            self.connection.commit()
        except db.Error, e:
            return 0
        return 1

    def get_current_weather(self, mobnum, ussd=None):
        sql = '''
            select 
                m.name, w.text
            from 
                sender_weathertext w, sender_mailing m
            where 
                m.id = %(mailing_id)s
                and mailing_id = m.id
                and NOW() between time_from and time_to
            limit 1
        '''
        try:
            mailing_id = self.get_mailing_id(mobnum) if ussd is None else self.get_mailing_id_ussd(mobnum)
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
            bwc_location_code = BWCCity(mobnum)
            self.cursor.execute(sql_bwc_code, { "bwc_location_code": bwc_location_code, })
            row = self.cursor.fetchone()
            self.connection.commit()
            if row:
                return row[0]

            self.cursor.execute(sql_mailing_id, { "mobnum": mobnum, })
            row = self.cursor.fetchone()
            self.connection.commit()
            if row:
                return row[0]

            return None

        except db.Error, e:
            self.raise_error(e)

    def get_mailing_id_ussd(self, mobnum):
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

            bwc_location_code = BWCCity(mobnum)
            self.cursor.execute(sql_bwc_code, { "bwc_location_code": bwc_location_code, })
            row = self.cursor.fetchone()
            self.connection.commit()
            if row:
                return row[0]

            return None

        except db.Error, e:
            self.raise_error(e)

    def subscribe(self, mobnum, mailing_id):
        sql_select = '''
            select count(*) from sender_subscriber where mobnum = %(mobnum)s and status = 0
        '''

        sql_insert = '''
            insert into sender_subscriber
                (mobnum, mailing_id, status, create_date, subs_time)
            values
                (%(mobnum)s, %(mailing_id)s, 0, NOW(), "18:30")
        '''

        sql_update = '''
            update
                sender_subscriber
            set
                mailing_id = %(mailing_id)s
            where
                mobnum = %(mobnum)s
        '''
        try:
            self.cursor.execute(sql_select, {
                'mobnum': mobnum,
            })
            row = self.cursor.fetchone()
            if row[0] == 0:
                self.cursor.execute(sql_insert, {
                    'mobnum': mobnum,
                    'mailing_id': mailing_id,
                })
                # send help
                self.add_new_task(mobnum, u'help', u'Вы подписались на погоду 818. Прогноз доставляется в 18:30 ежедневно. Устанавливайте любое время доставки. Например: при наборе *818*10# - погода будет отправляться в 10:00 утра. Стоимость 1 р. в сутки.', 0)
            else:
                self.cursor.execute(sql_update, {
                    'mailing_id': mailing_id,
                    'mobnum': mobnum,
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
                id, mobnum, out_text, in_text
            from
                sender_smstask
            where
                status = 0
                and delivery_date <= NOW()
            limit 10
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

    def get_evening_weather(self, mailing_id):
        sql0 = '''
            select 
                 max(CAST(w.temperature AS SIGNED)),  min(CAST(w.temperature AS SIGNED))
            from
                sender_weathertext w
            where
                w.mailing_id = %(mailing_id)s
                and w.time_from between date(CONVERT_TZ(NOW(), @@session.time_zone, '+09:00'))+interval 24+7-9 hour and date(CONVERT_TZ(NOW(), @@session.time_zone, '+09:00'))+interval 24+23-9 hour
        '''

        sql1 = '''
            select 
                 max(CAST(w.temperature AS SIGNED)),  min(CAST(w.temperature AS SIGNED))
            from
                sender_weathertext w
            where
                w.mailing_id = %(mailing_id)s
                and w.time_from between date(CONVERT_TZ(NOW(), @@session.time_zone, '+09:00'))+interval 23-9 hour and date(CONVERT_TZ(NOW(), @@session.time_zone, '+09:00'))+interval 24+7-9 hour
        '''

        sql3 = '''
            select 
                m.name, w.wcondition, w.wind_direction, w.wind_speed, DATE_FORMAT(date(CONVERT_TZ(NOW(), @@session.time_zone, '+09:00'))+interval 24 hour, '%%e %%b')
            from
                sender_weathertext w, sender_mailing m
            where
                m.id = %(mailing_id)s
                and w.mailing_id = m.id
                and date(CONVERT_TZ(NOW(), @@session.time_zone, '+09:00'))+interval 37-9 hour between w.time_from and w.time_to
        '''

        sql4 = '''
            select 
                m.name, w.wcondition, w.wind_direction, w.wind_speed
            from
                sender_weathertext w, sender_mailing m
            where
                m.id = %(mailing_id)s
                and w.mailing_id = m.id
                and date(CONVERT_TZ(NOW(), @@session.time_zone, '+09:00'))+interval 24+4-9 hour between w.time_from and w.time_to
        '''

        try:
            self.cursor.execute(sql0, { 'mailing_id': mailing_id, })
            row = self.cursor.fetchone()
            self.connection.commit()
            max_t0, min_t0 = row
            max_t0 = '%+d' %  max_t0
            min_t0 = '%+d' %  min_t0        
            if max_t0 == min_t0:
                max_t0 = ''

            self.cursor.execute(sql1, { 'mailing_id': mailing_id, })
            row = self.cursor.fetchone()
            self.connection.commit()
            max_t1, min_t1 = row
            max_t1 = '%+d' %  max_t1
            min_t1 = '%+d' %  min_t1
            if max_t1 == min_t1:
                max_t1 = ''

            self.cursor.execute(sql3, { 'mailing_id': mailing_id, })
            row = self.cursor.fetchone()
            self.connection.commit()
            name, condition, wind_direction, wind_speed, date = row

            self.cursor.execute(sql4, { 'mailing_id': mailing_id, })
            row = self.cursor.fetchone()
            self.connection.commit()
            name1, condition1, wind_direction1, wind_speed1 = row
        except db.Error, e:
            #self.raise_error(e)
            return u''
        #if min_t0 and min_t1 and max_t0 and max_t1:
        return u'%s. Завтра, %s: %s %s, %s, ветер %s %s м/c. Сегодня ночью: %s %s, %s. Погода сейчас - звони *818#' % (name, date, min_t0, max_t0, condition, wind_direction, wind_speed, min_t1, max_t1, self.night_replace(condition1))
        #return u''

    def night_replace(self, condition):
        condition = condition.replace(u'солнечно', u'безоблачно')
        condition = condition.replace(u'ясно', u'безоблачно')
        return condition

    def get_time_weather(self, mailing_id, subs_time):
        subs_time = self._parse_time_from_message(str(subs_time).zfill(8)[0:5])
        h = int("%s%s" % (subs_time[0:2], subs_time[3:5]))
        if h > 1600:
            return self.get_evening_weather(mailing_id)
        else:
            return self.get_today_weather(mailing_id)

    def get_today_weather(self, mailing_id):
        sql0 = '''
            select 
                 max(CAST(w.temperature AS SIGNED)),  min(CAST(w.temperature AS SIGNED))
            from
                sender_weathertext w
            where
                w.mailing_id = %(mailing_id)s
                and w.time_from between date(CONVERT_TZ(NOW(), @@session.time_zone, '+09:00'))-interval 2 hour and date(CONVERT_TZ(NOW(), @@session.time_zone, '+09:00'))+interval 23-9 hour
        '''

        sql1 = '''
            select 
                 max(CAST(w.temperature AS SIGNED)),  min(CAST(w.temperature AS SIGNED))
            from
                sender_weathertext w
            where
                w.mailing_id = %(mailing_id)s
                and w.time_from between date(CONVERT_TZ(NOW(), @@session.time_zone, '+09:00'))+interval 24+7-9 hour and date(CONVERT_TZ(NOW(), @@session.time_zone, '+09:00'))+interval 24+23-9 hour
        '''

        sql2 = '''
            select 
                 max(CAST(w.temperature AS SIGNED)),  min(CAST(w.temperature AS SIGNED))
            from
                sender_weathertext w
            where
                w.mailing_id = %(mailing_id)s
                and w.time_from between date(CONVERT_TZ(NOW(), @@session.time_zone, '+09:00'))+interval 23-9 hour and date(CONVERT_TZ(NOW(), @@session.time_zone, '+09:00'))+interval 24+7-9 hour
        '''

        sql3 = '''
            select 
                m.name, w.wcondition, w.wind_direction, w.wind_speed
            from
                sender_weathertext w, sender_mailing m
            where
                m.id = %(mailing_id)s
                and w.mailing_id = m.id
                and date(CONVERT_TZ(NOW(), @@session.time_zone, '+09:00'))+interval 13-9 hour between w.time_from and w.time_to
        '''

        sql4 = '''
            select 
                m.name, w.wcondition, w.wind_direction, w.wind_speed, DATE_FORMAT(date(CONVERT_TZ(NOW(), @@session.time_zone, '+09:00'))+interval 24 hour, '%%e %%b')
            from
                sender_weathertext w, sender_mailing m
            where
                m.id = %(mailing_id)s
                and w.mailing_id = m.id
                and date(CONVERT_TZ(NOW(), @@session.time_zone, '+09:00'))+interval 37-9 hour between w.time_from and w.time_to
        '''

        try:
            self.cursor.execute(sql0, { 'mailing_id': mailing_id, })
            row = self.cursor.fetchone()
            self.connection.commit()
            max_t0, min_t0 = row
            max_t0 = '%+d' %  max_t0
            min_t0 = '%+d' %  min_t0
            if max_t0 == min_t0:
                max_t0 = ''

            self.cursor.execute(sql1, { 'mailing_id': mailing_id, })
            row = self.cursor.fetchone()
            self.connection.commit()
            max_t1, min_t1 = row
            max_t1 = '%+d' %  max_t1
            min_t1 = '%+d' %  min_t1
            if max_t1 == min_t1:
                max_t1 = ''

            self.cursor.execute(sql2, { 'mailing_id': mailing_id, })
            row = self.cursor.fetchone()
            self.connection.commit()
            max_t2, min_t2 = row
            max_t2 = '%+d' %  max_t2
            min_t2 = '%+d' %  min_t2
            if max_t2 == min_t2:
                max_t2 = ''

            self.cursor.execute(sql3, { 'mailing_id': mailing_id, })
            row = self.cursor.fetchone()
            self.connection.commit()
            name, condition, wind_direction, wind_speed = row

            self.cursor.execute(sql4, { 'mailing_id': mailing_id, })
            row = self.cursor.fetchone()
            self.connection.commit()
            name1, condition1, wind_direction1, wind_speed1, date1 = row
        except db.Error, e:
            #self.raise_error(e)
            return u''
        #if min_t0 and min_t1 and min_t2 and max_t0 and max_t1 and max_t2:
        return u'%s. Сегодня днем, %s %s, %s, ветер %s %s м/c. Завтра, %s: %s %s, %s, ветер %s %s м/c. Сегодня ночью: %s %s. Погода сейчас - звони *818#' % (name, min_t0, max_t0, condition, wind_direction, wind_speed, date1, min_t1, max_t1, condition1, wind_direction1, wind_speed1, min_t2, max_t2)
        #return u''

    def get_weather_subscribers(self):
        sql = '''
            select
                s.mobnum, s.id, s.mailing_id, m.name, s.subs_time
            from
                sender_subscriber s, sender_mailing m
            where 
                s.status = 0 -- подписан
                and m.id = s.mailing_id
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
                and m.id not in (select w.mailing_id from sender_weathertext w 
                    where m.id = w.mailing_id and w.time_from > NOW()+interval 40 hour)
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
            select count(*) from sender_weathertext where time_from = CONVERT_TZ(%(time_from)s, @@session.time_zone, '-09:00') and mailing_id = %(mailing_id)s
        '''
        try:
            self.cursor.execute(sql, { 'time_from': weather['time_from'], 'mailing_id': mailing_id })
        except db.Error, e:
            self.raise_error(e)
 
        row = self.cursor.fetchone()
        if int(row[0]) > 0:
            return -1

        sql = '''
            insert into sender_weathertext
                (mailing_id, text, temperature, wcondition, wind_direction, wind_speed, time_from, time_to, create_date, pressure)
            values
                (%(mailing_id)s, %(text)s, %(temperature)s, %(condition)s, %(wind_direction)s, %(wind_speed)s, CONVERT_TZ(%(time_from)s, @@session.time_zone, '-09:00'), CONVERT_TZ(%(time_to)s, @@session.time_zone, '-09:00')-interval 1 second, NOW(), %(pressure)s)
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

    def get_ussd_requests(self):
        sql = '''
            select 
                distinct mobnum
            from
                sender_smstask
            where
                in_text like '*818%%'
                and delivery_date > now()-interval 30 minute
        '''
        try:
            self.cursor.execute(sql, {})
            self.connection.commit()
        except db.Error, e:
            self.raise_error(e)
            return []
        return self.cursor.fetchall()

    def update_location(self, mobnum):
        sql_bwc_code = '''
            select
                id, name
            from
                sender_mailing
            where
                bwc_location_code = %(bwc_location_code)s
        '''
        try:
            bwc_location_code = BWCCity(mobnum)
            self.cursor.execute(sql_bwc_code, { "bwc_location_code": bwc_location_code, })
            row = self.cursor.fetchone()
            self.connection.commit()
            if row:
                self.subscribe(mobnum, row[0])

        except db.Error, e:
            self.raise_error(e)



def main(args=None):
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    tasker = dbSMSTask(db_config, logger)

    errors = 0
    tasker.clear_weather_texts()
    mailings = tasker.get_mailing_list()
    weather = yrnoWeather()
    for mailing in mailings:
        try:
            yrno_location, mailing_id = mailing
            for i, item in enumerate(weather.get_weather_by_hour(yrno_location.encode('UTF-8'))):
                if int(item['temperature']) >= 0:
                    item['temperature'] = '+%s' % item['temperature']

                tuple_time = time.strptime(item['time_from'].replace("-", ""), "%Y%m%dT%H:%M:%S")
                item['time_from'] = datetime.datetime(*tuple_time[:6])
                tuple_time = time.strptime(item['time_to'].replace("-", ""), "%Y%m%dT%H:%M:%S")
                item['time_to'] = datetime.datetime(*tuple_time[:6])
                item['text'] = u'%s° C, %s, %s ветер %s м/с' % (item['temperature'], item['condition'], item['wind_direction'], item['wind_speed'])
                tasker.add_weather_text(mailing_id, item)
        except:
            errors = errors + 1
    if errors > 0:
        send_mail('subs@foxthrottle.com', ['metasize@gmail.com'], 'subs', 'Got weather. \n\n Errors: %s' % (errors))

def subs():
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    errors = 0
    tasker = dbSMSTask(db_config, logger)

    # создаем рассылку
    subscribers = tasker.get_weather_subscribers()
    for subscriber in subscribers:
        try:
            mobnum, sid, mailing_id, name, subs_time = subscriber

            # weather by time
            text = tasker.get_time_weather(mailing_id, subs_time)
            send_date = "%s %s" % (str(datetime.datetime.now())[0:10], subs_time)
            tasker.add_new_task(mobnum, 'subs', text, 0, send_date)
        except Exception, e:
            errors = errors + 1

    send_mail('subs@foxthrottle.com', ['metasize@gmail.com'], 'subs', 'Subscribers created. \n\n Errors: %s' % (errors))

def ussd_location():
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    errors = 0
    tasker = dbSMSTask(db_config, logger)

    requests = tasker.get_ussd_requests()
    for request in requests:
        mobnum = request[0]
        tasker.update_location(mobnum)


if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print "Usage: main | subs"
        sys.exit(1)

    if sys.argv[1] == 'subs':
        subs()
    elif sys.argv[1] == 'ussd_location':
        ussd_location()
    else:
        main()
