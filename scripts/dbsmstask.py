#!/usr/bin/env python
# -*- coding: utf-8 -*-

import MySQLdb as db
import sys, re
import logging
import time
import datetime
from yrno_weather import yrnoWeather
from mail import send_mail
from soap_client import RTSoapClient

# db config
sys.path.append('/var/www/subs/')
from local_settings import DATABASES
db_config = DATABASES['default']

DEFAULT_TIMEZONE = "+08:00"
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

        mailing_id = self.get_mailing_id(mobnum)
        timezone = self._get_timezone_negative(mailing_id)

        sql = '''
            insert into sw_smstask
                (mobnum, in_text, out_text, delivery_date, status)
            values
                (%(mobnum)s, %(in_text)s, %(out_text)s, ifnull(CONVERT_TZ(%(delivery_date)s, @@session.time_zone, %(timezone)s), NOW()), %(status)s)
        '''
        try:
            self.cursor.execute(sql, {
                'mobnum': mobnum,
                'in_text': in_text,
                'out_text': out_text,
                'status': status,
                'delivery_date': delivery_date,
                'timezone': timezone,
            })
            self.connection.commit()
        except db.Error, e:
            self.raise_error(e)
            return -1
        return self.cursor.lastrowid

    def update_task(self, status, task_id='', message_id='', new_message_id=''):
        sql = '''
            update
                sw_smstask
            set
                status = %(status)s,
                message_id = %(new_message_id)s,
                sent_date = NOW()
            where
                message_id = %(message_id)s
                or id = %(task_id)s
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
        subs_time = re.sub("^(\*4181|\*418)", "", short_message)
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
                sw_subscriber
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
                sw_smstask
            where
                mobnum = %(mobnum)s
                and delivery_date > NOW()-interval 1 day
                and status = 0
        '''
        try:
            self.cursor.execute(sql, {
                'mobnum': mobnum,
            })
            self.connection.commit()
        except db.Error, e:
            return 0
        return 1

    def get_current_weather(self, mobnum):
        sql = '''
            select
                m.name, w.text, m.timezone
            from
                sw_weathertext w, sw_mailing m
            where
                m.id = %(mailing_id)s
                and w.mailing_id = m.id
                and NOW() between time_from and time_to
            limit 1
        '''

        sql1 = '''
            select
                 max(CAST(w.temperature AS SIGNED)),  min(CAST(w.temperature AS SIGNED))
            from
                sw_weathertext w
            where
                w.mailing_id = %(mailing_id)s
                and w.time_from between date(CONVERT_TZ(NOW(), @@session.time_zone, %(timezone)s))+interval 24+7-9 hour and date(CONVERT_TZ(NOW(), @@session.time_zone, %(timezone)s))+interval 24+23-9 hour
        '''
        try:
            mailing_id = self.get_mailing_id(mobnum)
            if mailing_id:
                self.cursor.execute(sql, { 'mailing_id': mailing_id, })
                row = self.cursor.fetchone()
                self.connection.commit()
                if row:
                    name, weather, timezone = row
                    self.cursor.execute(sql1, { 'mailing_id': mailing_id, 'timezone': timezone,})
                    row = self.cursor.fetchone()
                    self.connection.commit()
                    max_t1, min_t1 = row
                    max_t1 = '%+d' %  max_t1
                    min_t1 = '%+d' %  min_t1
                    if max_t1 == min_t1:
                        max_t1 = ''

                    if weather:
                        return mailing_id, (u'%s: %s. Завтра Д %s Н %s' % (name[0:10], weather, max_t1, min_t1))[0:70]
                return mailing_id, None
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
                sw_subscriber
            where
                mobnum = %(mobnum)s
            order by
                create_date desc
            limit 1
        '''
        try:
            self.cursor.execute(sql_mailing_id, { "mobnum": mobnum, })
            row = self.cursor.fetchone()
            self.connection.commit()
            if row:
                return row[0]
            else:
                return None
        except db.Error, e:
            self.raise_error(e)

    def get_mailing_id_by_city(self, city):
        sql = '''
            select
                id
            from
                sw_mailing
            where
                lower(%(name)s) like concat('%%', lower(name), '%%')
            limit 1
        '''
        try:
            self.cursor.execute(sql, { "name": city, })
            row = self.cursor.fetchone()
            self.connection.commit()
            if row:
                return row[0]
            else:
                return None
        except db.Error, e:
            self.raise_error(e)

    def rt_connect(self):
        return RTSoapClient(dict(username='amstudio', password='JHMaNf5S'))

    def is_rtsubscribe(self, mobnum):
        # Returns: contractID, state == 1 - subscribe, > 1 - not subscribe
        sql = '''
            select
                contract_id, contract_state
            from
                sw_subscriber
            where
                mobnum = %(mobnum)s
                and status = 0
        '''

        sql_update_contract = '''
            update
                sw_subscriber
            set
                contract_id = %(contract_id)s,
                contract_state = %(contract_state)s
            where
                mobnum = %(mobnum)s
        '''

        try:
            self.cursor.execute(sql, { "mobnum": mobnum, })
            row = self.cursor.fetchone()
            self.connection.commit()
            if row:
                contract_id, contract_state = row
                if contract_id and contract_id > 0:
                    client = self.rt_connect()
                    contract = client.request('contractState', { "contractID": contract_id })
                    if contract:
                        for c in contract.contracts:
                            if c.contractID == contract_id:
                                self.cursor.execute(sql_update_contract, { "mobnum": mobnum, "contract_id": c.contractID, "contract_state": c.state, })
                                self.connection.commit()
                                return c.contractID, c.state
            return 0, 0
        except db.Error, e:
            self.raise_error(e)

    def register_rtcontract(self, mobnum, platform, message):
        contract_id, contract_state = self.is_rtsubscribe(mobnum)
        if contract_id > 0 and contract_state == 1:
            return contract_id

        sql_get_requestid = '''
            select ifnull(max(request_id)+1, 10) from sw_subscriber
        '''

        sql_update_requestid = '''
            update
                sw_subscriber
            set
                request_id = %(request_id)s
            where
                mobnum = %(mobnum)s
        '''

        sql_update_contract = '''
            update
                sw_subscriber
            set
                contract_id = %(contract_id)s,
                contract_state = %(contract_state)s
            where
                mobnum = %(mobnum)s
        '''

        # typ: 1 - sms, 2 - ussd
        # number: 4181 - sms, 418 - ussd
        typ = 1
        number = '4181'
        if not message:
            message = '4181'

        if platform == 'USSD':
            typ = 2
            number = '418'

        try:
            self.cursor.execute(sql_get_requestid, { })
            row = self.cursor.fetchone()
            self.connection.commit()
            request_id = row[0]

            self.cursor.execute(sql_update_requestid, { "mobnum": mobnum, "request_id": request_id, })
            self.connection.commit()

            client = self.rt_connect()
            result = client.api.service.requestContract(request_id, mobnum, 1, 1, 2, '', { 'type': typ, 'number': number, 'message': message, })

            if result:
                self.cursor.execute(sql_update_contract, { "mobnum": mobnum, "contract_id": result.contractID, "contract_state": 1, })
                self.connection.commit()
                return result.contractID, result.status
            return 0
        except db.Error, e:
            self.raise_error(e)

    def unregister_rtcontract(self, mobnum):
        sql_update_contract = '''
            update
                sw_subscriber
            set
                contract_id = %(contract_id)s,
                contract_state = %(contract_state)s
            where
                mobnum = %(mobnum)s
        '''

        client = self.rt_connect()
        contract_id, contract_state = self.is_rtsubscribe(mobnum)
        if contract_id > 0:
            result = client.api.service.modifyContract(contract_id, 2, 2, '', { 'type': 1, 'number': '4181', 'message': 'stop', })
            if result:
                try:
                    self.cursor.execute(sql_update_contract, { "mobnum": mobnum, "contract_id": contract_id, "contract_state": 2, })
                    self.connection.commit()
                    return
                except db.Error, e:
                    self.raise_error(e)
        return


    def is_subscribe(self, mobnum):
        # Returns: 1 - subscribe, 0 - not subscribe, -1 - was subs
        sql_subscribe = '''
            select count(*) from sw_subscriber where mobnum = %(mobnum)s and status = 0
        '''

        sql_subscribe_0 = '''
            select count(*) from sw_subscriber where mobnum = %(mobnum)s
        '''
        try:
            self.cursor.execute(sql_subscribe, { "mobnum": mobnum, })
            row = self.cursor.fetchone()
            self.connection.commit()
            if row[0] > 0:
                self.cursor.execute(sql_subscribe, { "mobnum": mobnum, })
                row = self.cursor.fetchone()
                self.connection.commit()
                return 1
            else:
                self.cursor.execute(sql_subscribe_0, { "mobnum": mobnum, })
                row = self.cursor.fetchone()
                self.connection.commit()
                if row[0] > 0:
                    return -1 # exist
                else:
                    return 0
        except db.Error, e:
            self.raise_error(e)

    def subscribe(self, mobnum, mailing_id, typ, message):
        if not mailing_id or not mobnum: # or mobnum in ('79500586318'):
            return 0

        sql = '''
            select name from sw_mailing where id = %(mailing_id)s
        '''

        sql_insert = '''
            insert into sw_subscriber
                (mobnum, mailing_id, status, create_date, subs_time)
            values
                (%(mobnum)s, %(mailing_id)s, 0, NOW(), "20:30")
        '''

        sql_update = '''
            update
                sw_subscriber
            set
                mailing_id = %(mailing_id)s,
                status = 0
            where
                mobnum = %(mobnum)s
        '''
        try:
            is_subscribe = self.is_subscribe(mobnum)
            contract_id, contract_state = self.is_rtsubscribe(mobnum)
            if is_subscribe <= 0 or contract_state != 1:
                if is_subscribe == 0:
                    self.cursor.execute(sql_insert, {
                        'mobnum': mobnum,
                        'mailing_id': mailing_id,
                    })

                if is_subscribe < 0:
                    self.cursor.execute(sql_update, {
                        'mobnum': mobnum,
                        'mailing_id': mailing_id,
                    })

                # send help
                self.register_rtcontract(mobnum, typ, message)
                self.cursor.execute(sql, {
                    'mailing_id': mailing_id,
                })
                row = self.cursor.fetchone()
                self.add_new_task(mobnum, u'help', u'Оформлена подписка на прогноз погоды %s. Доставка в 20:30 ежедневно. Смена времени отправки *418*время#. Отписка *418*0#. Стоимость 2р/день' % row[0], 0)
                return 2
            else:
                self.cursor.execute(sql_update, {
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
                sw_subscriber
            set
                status = 1
            where
                mobnum = %(mobnum)s
        '''
        self.unregister_rtcontract(mobnum)
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
                t.id, t.mobnum, t.out_text, t.in_text
            from
                sw_smstask t, sw_subscriber s
            where
                t.status = 0 
                and t.delivery_date between NOW()-interval 2 hour and NOW()
                and t.mobnum = s.mobnum 
                and s.status = 0  
                and s.contract_state = 1 
            limit 15
        '''
        try:
            self.cursor.execute(sql, {})
            self.connection.commit() # or will be use a cache
        except db.Error, e:
            self.raise_error(e)
            return []

        return self.cursor.fetchall()

    def check_spam(self, mobnum):
        sql = '''
            select
                count(*)
            from
                sw_smstask
            where
                mobnum = %(mobnum)s
                and delivery_date > NOW()-interval 1 day
        '''
        try:
            self.cursor.execute(sql, { 'mobnum': mobnum, })
            self.connection.commit() # or will be use a cache
            row = self.cursor.fetchone()
        except db.Error, e:
            self.raise_error(e)
            return 0
        return row[0]

    def raise_error(self, error):
        self.connection_state = 0
        self.logger.critical(error)
        raise

    def _get_timezone(self, mailing_id):
        sql = '''
            select
                timezone
            from
                sw_mailing
            where
                id = %(mailing_id)s
        '''
        try:
            self.cursor.execute(sql, { 'mailing_id': mailing_id, })
            self.connection.commit() # or will be use a cache
            row = self.cursor.fetchone()
        except db.Error, e:
            self.raise_error(e)
            return DEFAULT_TIMEZONE
        if row:
            return row[0]
        else:
            return DEFAULT_TIMEZONE


    def _get_timezone_negative(self, mailing_id):
        timezone = self._get_timezone(mailing_id)
        return timezone.replace('+', '-')

    def get_evening_weather(self, mailing_id):
        timezone = self._get_timezone(mailing_id)

        sql0 = '''
            select
                 max(CAST(w.temperature AS SIGNED)),  min(CAST(w.temperature AS SIGNED))
            from
                sw_weathertext w
            where
                w.mailing_id = %(mailing_id)s
                and w.time_from between date(CONVERT_TZ(NOW(), @@session.time_zone, %(timezone)s))+interval 24+7-9 hour and date(CONVERT_TZ(NOW(), @@session.time_zone, %(timezone)s))+interval 24+23-9 hour
        '''

        sql1 = '''
            select
                 max(CAST(w.temperature AS SIGNED)),  min(CAST(w.temperature AS SIGNED))
            from
                sw_weathertext w
            where
                w.mailing_id = %(mailing_id)s
                and w.time_from between date(CONVERT_TZ(NOW(), @@session.time_zone, %(timezone)s))+interval 23-9 hour and date(CONVERT_TZ(NOW(), @@session.time_zone, %(timezone)s))+interval 24+7-9 hour
        '''

        sql3 = '''
            select
                m.name, w.wcondition, w.wind_direction, w.wind_speed, DATE_FORMAT(date(CONVERT_TZ(NOW(), @@session.time_zone, %(timezone)s))+interval 24 hour, '%%d.%%m'), w.pressure-40
            from
                sw_weathertext w, sw_mailing m
            where
                m.id = %(mailing_id)s
                and w.mailing_id = m.id
                and date(CONVERT_TZ(NOW(), @@session.time_zone, %(timezone)s))+interval 37-9 hour between w.time_from and w.time_to
        '''

        sql4 = '''
            select
                m.name, w.wcondition, w.wind_direction, w.wind_speed
            from
                sw_weathertext w, sw_mailing m
            where
                m.id = %(mailing_id)s
                and w.mailing_id = m.id
                and date(CONVERT_TZ(NOW(), @@session.time_zone, %(timezone)s))+interval 24+4-9 hour between w.time_from and w.time_to
        '''

        try:
            self.cursor.execute(sql0, { 'mailing_id': mailing_id, 'timezone': timezone, })
            row = self.cursor.fetchone()
            self.connection.commit()
            max_t0, min_t0 = row
            max_t0 = '%+d' %  max_t0
            min_t0 = '%+d' %  min_t0
            if max_t0 == min_t0:
                max_t0 = ''

            self.cursor.execute(sql1, { 'mailing_id': mailing_id, 'timezone': timezone, })
            row = self.cursor.fetchone()
            self.connection.commit()
            max_t1, min_t1 = row
            max_t1 = '%+d' %  max_t1
            min_t1 = '%+d' %  min_t1
            if max_t1 == min_t1:
                max_t1 = ''

            self.cursor.execute(sql3, { 'mailing_id': mailing_id, 'timezone': timezone, })
            row = self.cursor.fetchone()
            self.connection.commit()
            name, condition, wind_direction, wind_speed, date, pressure = row

            self.cursor.execute(sql4, { 'mailing_id': mailing_id, 'timezone': timezone, })
            row = self.cursor.fetchone()
            self.connection.commit()
            name1, condition1, wind_direction1, wind_speed1 = row
        except db.Error, e:
            return u''
        return (u'%s %s: %s, Д %s Н %s, %s ветер %sм/с, %d' % (name[0:10], date, condition, max_t0, min_t1, wind_direction, wind_speed, pressure))[0:70]

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
        timezone = self._get_timezone(mailing_id)

        sql0 = '''
            select
                 max(CAST(w.temperature AS SIGNED)),  min(CAST(w.temperature AS SIGNED))
            from
                sw_weathertext w
            where
                w.mailing_id = %(mailing_id)s
                and w.time_from between date(CONVERT_TZ(NOW(), @@session.time_zone, %(timezone)s))-interval 2 hour and date(CONVERT_TZ(NOW(), @@session.time_zone, %(timezone)s))+interval 23-9 hour
        '''

        sql1 = '''
            select
                 max(CAST(w.temperature AS SIGNED)),  min(CAST(w.temperature AS SIGNED))
            from
                sw_weathertext w
            where
                w.mailing_id = %(mailing_id)s
                and w.time_from between date(CONVERT_TZ(NOW(), @@session.time_zone, %(timezone)s))+interval 24+7-9 hour and date(CONVERT_TZ(NOW(), @@session.time_zone, %(timezone)s))+interval 24+23-9 hour
        '''

        sql2 = '''
            select
                 max(CAST(w.temperature AS SIGNED)),  min(CAST(w.temperature AS SIGNED))
            from
                sw_weathertext w
            where
                w.mailing_id = %(mailing_id)s
                and w.time_from between date(CONVERT_TZ(NOW(), @@session.time_zone, %(timezone)s))+interval 23-9 hour and date(CONVERT_TZ(NOW(), @@session.time_zone, %(timezone)s))+interval 24+7-9 hour
        '''

        sql3 = '''
            select
                m.name, w.wcondition, w.wind_direction, w.wind_speed, w.pressure-40, DATE_FORMAT(date(CONVERT_TZ(NOW(), @@session.time_zone, %(timezone)s))+interval 13-9 hour, '%%d.%%m')
            from
                sw_weathertext w, sw_mailing m
            where
                m.id = %(mailing_id)s
                and w.mailing_id = m.id
                and date(CONVERT_TZ(NOW(), @@session.time_zone, %(timezone)s))+interval 13-9 hour between w.time_from and w.time_to
        '''

        sql4 = '''
            select
                m.name, w.wcondition, w.wind_direction, w.wind_speed, DATE_FORMAT(date(CONVERT_TZ(NOW(), @@session.time_zone, %(timezone)s))+interval 24 hour, '%%d.%%m')
            from
                sw_weathertext w, sw_mailing m
            where
                m.id = %(mailing_id)s
                and w.mailing_id = m.id
                and date(CONVERT_TZ(NOW(), @@session.time_zone, %(timezone)s))+interval 37-9 hour between w.time_from and w.time_to
        '''

        try:
            self.cursor.execute(sql0, { 'mailing_id': mailing_id, 'timezone': timezone, })
            row = self.cursor.fetchone()
            self.connection.commit()
            max_t0, min_t0 = row
            max_t0 = '%+d' %  max_t0
            min_t0 = '%+d' %  min_t0
            if max_t0 == min_t0:
                max_t0 = ''

            self.cursor.execute(sql1, { 'mailing_id': mailing_id, 'timezone': timezone, })
            row = self.cursor.fetchone()
            self.connection.commit()
            max_t1, min_t1 = row
            max_t1 = '%+d' %  max_t1
            min_t1 = '%+d' %  min_t1
            if max_t1 == min_t1:
                max_t1 = ''

            self.cursor.execute(sql2, { 'mailing_id': mailing_id, 'timezone': timezone, })
            row = self.cursor.fetchone()
            self.connection.commit()
            max_t2, min_t2 = row
            max_t2 = '%+d' %  max_t2
            min_t2 = '%+d' %  min_t2
            if max_t2 == min_t2:
                max_t2 = ''

            self.cursor.execute(sql3, { 'mailing_id': mailing_id, 'timezone': timezone, })
            row = self.cursor.fetchone()
            self.connection.commit()
            name, condition, wind_direction, wind_speed, pressure, date0 = row

            self.cursor.execute(sql4, { 'mailing_id': mailing_id, 'timezone': timezone, })
            row = self.cursor.fetchone()
            self.connection.commit()
            name1, condition1, wind_direction1, wind_speed1, date1 = row
        except db.Error, e:
            return u''
        return (u'%s: %s, %s, ветер %s %sм/с, %d. Завтра: Д %s Н %s' % (name[0:10], max_t0, condition, wind_direction, wind_speed, pressure, max_t1, min_t2))[0:70]

    def get_weather_subscribers(self):
        sql = '''
            select
                s.mobnum, s.id, s.mailing_id, m.name, s.subs_time
            from
                sw_subscriber s, sw_mailing m
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
                sw_mailing m
            where
                m.yrno_location_code is not null
                and m.id not in (
                    select w.mailing_id from sw_weathertext w
                    where m.id = w.mailing_id and w.time_from > NOW()+interval 40 hour
                )
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
            delete from sw_weathertext where create_date < date_sub(NOW(), interval 2 day)
        '''
        try:
            self.cursor.execute(sql, {})
            self.connection.commit()
        except db.Error, e:
            self.raise_error(e)

    def refill_log(self):
        sql_select = '''
            select id, mobnum, in_text, out_text, delivery_date, sent_date, status, message_id, error from sw_smstask where delivery_date < NOW() - interval 1 day limit 50000
        '''

        sql_from_delete = '''
            delete from sw_smstask where id = %(id)s
        '''

        sql_to_insert = '''
            insert into sw_smstasklog
                (mobnum, in_text, out_text, delivery_date, sent_date, status, message_id, error)
            values
                (%(mobnum)s, %(in_text)s, %(out_text)s, %(delivery_date)s, %(sent_date)s, %(status)s, %(message_id)s, %(error)s)
        '''
        try:
            self.cursor.execute(sql_select, {})
            rows = self.cursor.fetchall()
            for row in rows:
                (id, mobnum, in_text, out_text, delivery_date, sent_date, status, message_id, error) = row
                self.cursor.execute(sql_to_insert, {
                    'mobnum': mobnum,
                    'in_text': in_text,
                    'out_text': out_text,
                    'delivery_date': delivery_date,
                    'sent_date': sent_date,
                    'status': status,
                    'message_id': message_id,
                    'error': error,
                })
                self.cursor.execute(sql_from_delete, { 'id': id, })

            self.connection.commit()
        except db.Error, e:
            self.raise_error(e)

    def add_weather_text(self, mailing_id, weather):
        timezone = self._get_timezone_negative(mailing_id)

        sql = '''
            select count(*) from sw_weathertext where time_from = CONVERT_TZ(%(time_from)s, @@session.time_zone, %(timezone)s) and mailing_id = %(mailing_id)s
        '''
        try:
            self.cursor.execute(sql, { 'time_from': weather['time_from'], 'mailing_id': mailing_id, 'timezone': timezone, })
        except db.Error, e:
            self.raise_error(e)

        row = self.cursor.fetchone()
        if int(row[0]) > 0:
            return -1

        sql = '''
            insert into sw_weathertext
                (mailing_id, text, temperature, wcondition, wind_direction, wind_speed, time_from, time_to, create_date, pressure)
            values
                (%(mailing_id)s, %(text)s, %(temperature)s, %(condition)s, %(wind_direction)s, %(wind_speed)s, CONVERT_TZ(%(time_from)s, @@session.time_zone, %(timezone)s), CONVERT_TZ(%(time_to)s, @@session.time_zone, %(timezone)s)-interval 1 second, NOW(), %(pressure)s)
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
                'timezone': timezone,
            })
            self.connection.commit()
        except db.Error, e:
            self.raise_error(e)
            return -1
        return self.cursor.lastrowid




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
                item['text'] = u'%s, %s, %s ветер %sм/с' % (item['temperature'], item['condition'], item['wind_direction'], item['wind_speed'])
                tasker.add_weather_text(mailing_id, item)
        except:
            errors = errors + 1
    if errors > 0:
        send_mail('subs@foxthrottle.com', ['usayplz@gmail.com'], 'subs', 'Got weather. \n\n Errors: %s' % (errors))

def subs():
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    errors = 0
    tasker = dbSMSTask(db_config, logger)

    # clean old
    sql = ''' update sw_smstask set status = -3 where status = 0 '''
    tasker.cursor.execute(sql, {})
    tasker.connection.commit()

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

    send_mail('subs@foxthrottle.com', ['usayplz@gmail.com'], 'subs', 'Subscribers created. \n\n Errors: %s' % (errors))


def test():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    tasker = dbSMSTask(db_config, logger)
    # print tasker.get_today_weather(10)
    # print tasker.unsubscribe('79021700986')
    print tasker.unsubscribe('79500551827')
    #print tasker.subscribe('79500923584', 258, 'SMS', '4181')

def refill():
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    tasker = dbSMSTask(db_config, logger)
    tasker.refill_log()

def lastpayment():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    errors = 0
    tasker = dbSMSTask(db_config, logger)

    sql = '''
        select
            s.mobnum, s.request_id, s.contract_id, s.contract_state
        from
            sw_subscriber s
        where
            -- s.status = 0 and
            s.contract_id > 0
    '''

    sql_update_contract = '''
        update
            sw_subscriber
        set
            contract_id = %(contract_id)s,
            contract_state = %(contract_state)s
        where
            mobnum = %(mobnum)s
    '''

    sql_set_lastpayment = '''
        insert into sw_lastpayment
            (mobnum, payment_date)
        values
            (%(mobnum)s, %(lastpayment)s)
    '''

    sql_check_lastpayment = '''
        select count(*) from sw_lastpayment where mobnum = %(mobnum)s and payment_date = %(lastpayment)s;
    '''

    tasker.cursor.execute(sql, { })
    subscribers = tasker.cursor.fetchall()

    SEND_CONTRACT_SIZE = 100
    for i in xrange(0, len(subscribers), SEND_CONTRACT_SIZE):
        subs = subscribers[i:i+SEND_CONTRACT_SIZE]
        contract_ids = [str(x[2]) for x in subs]
        mobnums_dict = dict((str(contract_id), mobnum) for mobnum, request_id, contract_id, contract_state in subs)

        try:
            client = tasker.rt_connect()
            contract = client.request('contractState', { "contractID": contract_ids })
            if contract:
                for c in contract.contracts:
                    mobnum = mobnums_dict[str(c.contractID)]
                    tasker.cursor.execute(sql_update_contract, { "mobnum": mobnum, "contract_id": c.contractID, "contract_state": c.state, })
                    tasker.connection.commit()
                    if c.lastPaid:
                        lastpayment = str(c.lastPaid)[0:10]
                        tasker.cursor.execute(sql_check_lastpayment, { "mobnum": mobnum, "lastpayment": lastpayment, })
                        row = tasker.cursor.fetchone()
                        if row[0] == 0:
                            print "insert: ", mobnum
                            tasker.cursor.execute(sql_set_lastpayment, { "mobnum": mobnum, "lastpayment": lastpayment, })
                            tasker.connection.commit()
        except Exception, e:
            errors = errors + 1

    if errors > 0:
        send_mail('subs@foxthrottle.com', ['usayplz@gmail.com'], 'subs', 'lastpayment. \n\n Errors: %s' % (errors))


if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print "Usage: main | subs"
        sys.exit(1)

    if sys.argv[1] == 'subs':
        subs()
    elif sys.argv[1] == 'refill':
        refill()
    elif sys.argv[1] == 'test':
        test()
    elif sys.argv[1] == 'imports':
        imports()
    elif sys.argv[1] == 'lastpayment':
        lastpayment()
    elif sys.argv[1] == 'main':
        main()
    else:
        sys.exit(1)
