#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3 as db

class dbSMSTask(object):
    connection = None
    cursor = None

    def __init__(self, connection_string):
        try:
            self.connection = db.connect(connection_string)
            self.cursor = connection.cursor()
        except db.Error, e:
            print e
            return 2

    def __del__(self):
        self.connection.commit()
        self.connection.close()

    def add_new_task(self, mobnum, message_id):
        status = 0
        weather = u'good'

        sql = '''
            insert into sender_smstask 
                (mobnum, sms_text, status, message_id)
            values 
                (:mobnum, :sms_text, :status, :message_id)
        '''
        try:
            self.cursor.execute(sql, {
                "mobnum": mobnum,
                "sms_text": weather,
                "status": status, 
                "message_id": message_id
            })
            self.connection.commit()
        except db.Error, e:
            print e
            return 2

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
            print e
            return 2


def main(args):
    tasker = dbSMSTask('../local.db')
    tasker.add_new_task('9021702030', 123456)

if __name__ == '__main__':
    main()
