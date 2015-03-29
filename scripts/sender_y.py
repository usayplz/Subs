#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, logging, datetime, time
from twisted.internet import reactor, defer, task
from smpp.twisted.client import SMPPClientTransceiver, SMPPClientService
from smpp.twisted.config import SMPPClientConfig
from twisted.python import failure
from smpp.pdu.operations import *
from smpp.pdu.pdu_types import *
import dbsmstask, pid
import re

import MySQLdb as db

# db config
sys.path.append('/var/www/subs/')
from local_settings import DATABASES


class SMPP(object):
    ESME_NUM = 'BWC'
    SOURCE_ADDR_TON = AddrTon.ALPHANUMERIC
    SOURCE_ADDR_NPI = AddrNpi.UNKNOWN

    #ESME_NUM = '8181'
    #SOURCE_ADDR_TON = AddrTon.UNKNOWN
    #SOURCE_ADDR_NPI = AddrNpi.ISDN


    DEST_ADDR_TON = AddrTon.INTERNATIONAL
    DEST_ADDR_NPI = AddrNpi.ISDN

    def __init__(self, smpp_config, db_config, logger):
        self.smpp_config = smpp_config
        self.db_config = db_config
        self.logger = logger
        self.smstask = dbsmstask.dbSMSTask(db_config, logger)
        self.mark = 0

    @defer.inlineCallbacks
    def run(self):
        try:
            self.smpp = yield SMPPClientTransceiver(self.smpp_config, self.handleMsg).connectAndBind()
            self.lc_send_all = task.LoopingCall(self.send_all)
            self.lc_send_all.start(5)
            # self.send_sms(self.smpp, '79021702030', u'omaho').addBoth(self.message_sent)
            #self.send_city()
            yield self.smpp.getDisconnectedDeferred()
        except Exception, e:
            self.logger.critical(e)
            raise
        finally:
            reactor.stop()

    def send_all(self):
        sms_text = u'Погода для нас.п. "%s". Подписка и текущая температура ЗВОНИ *418#. 2 р/день. Отписка *418*0#.'
        self.cursor = None
        self.connection = None
        try:
            self.connection = db.connect(
                host=self.db_config.get('HOST'),
                user=self.db_config.get('USER'), 
                passwd=self.db_config.get('PASSWORD'), 
                db=self.db_config.get('NAME'), 
                charset='utf8',
            )

            self.cursor = self.connection.cursor()
            self.cursor.execute('SET SESSION query_cache_type = OFF')
            self.cursor.execute('SET TIME_ZONE = "+00:00"')
            self.cursor.execute('SET lc_time_names = "ru_RU"')
        except db.Error, e:
            raise_error(e)

        # d.sent is NULL and d.bwc_location_code not in (1,2,3,127) 
        # d.name = '79021702030'
        # --and d.bwc_location_code in (1,2,3,127)
        sql = '''
            select d.id, d.name, m.name
            from sender_data d, sender_mailing m
            where d.bwc_location_code in (1,3) and d.sent = 2
            and d.bwc_location_code = m.bwc_location_code limit 30
        '''
        sqlu = '''
            update sender_data set sent = 1 where id = %(id)s
        '''

        self.cursor.execute(sql, { })
        rows = self.cursor.fetchall()
        for row in rows:
            id, mobnum, city = row
            self.cursor.execute(sqlu, { "id": id })
            self.connection.commit()
            text = sms_text % city
            self.logger.info(mobnum)
            self.logger.info(text)
            self.send_sms(self.smpp, mobnum, text).addBoth(self.message_sent)

        self.connection.close()

    def handleMsg(self, smpp, pdu):
        return

    def send_sms(self, smpp, source_addr, short_message, from_num=None):
        """params:
            report: on
            encoding: UCS2
        """
        short_message = short_message.encode('utf_16_be')
        if from_num is None:
            from_num = self.ESME_NUM
        submit_pdu = SubmitSM(
            source_addr=from_num,
            destination_addr=source_addr,
            message_payload=short_message,
            source_addr_ton=self.SOURCE_ADDR_TON,
            source_addr_npi=self.SOURCE_ADDR_NPI,
            dest_addr_ton=self.DEST_ADDR_TON,
            dest_addr_npi=self.DEST_ADDR_NPI,
            esm_class=EsmClass(EsmClassMode.DEFAULT, EsmClassType.DEFAULT),
            protocol_id=0,
            registered_delivery=RegisteredDelivery(RegisteredDeliveryReceipt.SMSC_DELIVERY_RECEIPT_REQUESTED),
            replace_if_present_flag=ReplaceIfPresentFlag.DO_NOT_REPLACE,
            data_coding=DataCoding(DataCodingScheme.DEFAULT, DataCodingDefault.UCS2),
        )
        return smpp.sendDataRequest(submit_pdu)

    def message_sent(self, *args, **kwargs):
        instance = args[0]
        if not isinstance(instance, failure.Failure):
            # new_message_id = instance.response.params.get('message_id', 0)
            # self.smstask.update_task(1, task_id, '', new_message_id)
            self.logger.info('Message sent')
        else:
            # self.smstask.update_task(-1, task_id, '', -1)
            self.logger.info('Error send')
            #self.logger.info(instance)


def critical(msg, *args, **kwargs):
    #logger.error(msg)
    reactor.stop()


if __name__ == '__main__':
    # check pid
    PID = 'sender_y.pid'
    if pid.check_pid(int(pid.read_pid(PID))):
        print "Already running %s" % (PID,)
        exit(0)
    else:
        pid.write_pid(PID)

    # logger
    log_file = 'sender_y.log'
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)-15s %(levelname)s %(message)s",
        filename=log_file
    )
    logger = logging.getLogger(__name__)
    logger.critical = critical

    # start
    logger.info('[START PROGRAM]')
    db_config = DATABASES['default']
    smpp_config = SMPPClientConfig(
        host='81.18.113.146', port=3204, username='amstudio2', password='Yrj39sVa', enquireLinkTimerSecs=120, responseTimerSecs=300, )
    SMPP(smpp_config, db_config, logger).run()
    reactor.run()
