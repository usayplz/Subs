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

# db config
sys.path.append('/var/www/subs/')
from local_settings import DATABASES


class SMPP(object):
    ESME_NUM = '8181'
    SOURCE_ADDR_TON = AddrTon.UNKNOWN
    SOURCE_ADDR_NPI = AddrNpi.ISDN
    DEST_ADDR_TON = AddrTon.INTERNATIONAL
    DEST_ADDR_NPI = AddrNpi.ISDN

    def __init__(self, smpp_config, db_config, logger):
        self.smpp_config = smpp_config
        self.db_config = db_config
        self.logger = logger
        self.smstask = dbsmstask.dbSMSTask(db_config, logger)

    @defer.inlineCallbacks
    def run(self):
        try:
            self.smpp = yield SMPPClientTransceiver(self.smpp_config, self.handleMsg).connectAndBind()
            self.lc_send_all = task.LoopingCall(self.send_all)
            self.lc_send_all.start(5)
            yield self.smpp.getDisconnectedDeferred()
        except Exception, e:
            self.logger.critical(e)
            raise
        finally:
            reactor.stop()

    def handleMsg(self, smpp, pdu):
        source_addr = pdu.params.get('source_addr', '')
        short_message = pdu.params.get('short_message', '')
        message_state = pdu.params.get('message_state', None)
        message_id = pdu.params.get('receipted_message_id', -1)
        data_coding = pdu.params.get('data_coding', -1)

        self.logger.info('PDU = %s' % pdu)

        if pdu.commandId == CommandId.deliver_sm:
            if message_state is None:
                if data_coding.schemeData == DataCodingDefault.SMSC_DEFAULT_ALPHABET:
                    short_message = unicode(short_message, 'ascii')
                elif data_coding.schemeData == DataCodingDefault.IA5_ASCII:
                    short_message = unicode(short_message, 'ascii')
                elif data_coding.schemeData == DataCodingDefault.UCS2:
                    short_message = unicode(short_message, 'UTF-16BE')
                elif data_coding.schemeData == DataCodingDefault.LATIN_1:
                    short_message = unicode(short_message, 'latin_1')

                # checking
                if re.findall(u"стоп|stop|off|-pogoda|-погода", short_message.lower(), re.UNICODE):
                    self.smstask.unsubscribe(source_addr)
                    out_text = u'Вы отписаны от ежедневной погоды. Спасибо за использование сервиса.'
                    task_id = self.smstask.add_new_task(source_addr, short_message, out_text, 1)
                    self.send_sms(smpp, source_addr, out_text).addBoth(self.message_sent, task_id)
                else:
                    # send message and subscribe
                    (mailing_id, weather) = self.smstask.get_current_weather(source_addr)
                    if weather:
                        task_id = self.smstask.add_new_task(source_addr, short_message, weather, 1)
                        self.send_sms(smpp, source_addr, weather).addBoth(self.message_sent, task_id)
                        self.smstask.subscribe(source_addr, mailing_id)
                        self.logger.info('new task (id, mobnum, text): %s, %s, %s' % (task_id, source_addr, weather))
                    elif mailing_id:
                        out_text = u'Для Вашего нас. пункта нет погоды.'
                        task_id = self.smstask.add_new_task(source_addr, short_message, out_text, 1)
                        self.send_sms(smpp, source_addr, out_text).addBoth(self.message_sent, task_id)
                        self.logger.info('ERROR: cannot get weather (id, mobnum, text): %s, %s, %s' % (task_id, source_addr, weather))
                    else:
                        out_text = u'Нас. пункт не определен. Отправьте смс с названием на 8181.'
                        task_id = self.smstask.add_new_task(source_addr, short_message, out_text, 1)
                        self.send_sms(smpp, source_addr, out_text).addBoth(self.message_sent, task_id)
                        self.logger.info('ERROR: cannot get weather (id, mobnum, text): %s, %s, %s' % (task_id, source_addr, weather))

            elif message_state == MessageState.DELIVERED:
                self.smstask.update_task(2, '', message_id, message_id)
                self.logger.info('DELIVERED: %s' % message_id)
            elif message_state == MessageState.UNDELIVERABLE:
                self.smstask.update_task(-2, '', message_id, message_id)
                self.logger.info('UNDELIVERED: %s' % message_id)

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
        task_id = args[1]
        if not isinstance(instance, failure.Failure):
            new_message_id = instance.response.params.get('message_id', 0)
            self.smstask.update_task(1, task_id, '', new_message_id)
            self.logger.info('Message sent task id: %s' % task_id)
        else:
            self.smstask.update_task(-1, task_id, '', -1)
            self.logger.info('Error send task id: %s' % task_id)
            self.logger.info(instance)

    def send_all(self):
        tasks = self.smstask.check_tasks()
        for task in tasks:
            task_id, mobnum, out_text, in_text = task
            self.logger.info('new task (id, mobnum, text): %s, %s, %s' % (task_id, mobnum, out_text))
            self.smstask.update_task(-1, task_id, '', -1)
            from_num = self.ESME_NUM
            if in_text == u'help':
                from_num = '8180'

            if out_text:
                d = self.send_sms(self.smpp, mobnum, out_text, from_num)
                d.addBoth(self.message_sent, task_id)
            else:
                self.logger.error('ERROR: subs has not weather! task_id, mobnum = %s, %s' % (task_id, mobnum))


def critical(msg, *args, **kwargs):
    logger.error(msg)
    reactor.stop()


if __name__ == '__main__':
    # check pid
    PID = 'sender.pid'
    if pid.check_pid(int(pid.read_pid(PID))):
        print "Already running %s" % (PID,)
        exit(0)
    else:
        pid.write_pid(PID)

    # logger
    log_file = os.path.join(os.path.dirname(__file__), 'logs', '%s_%s' % (datetime.date.today().strftime('%d%m%Y'), 'sender.log'))
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
        host='81.18.113.146', port=3202, username='272', password='Ha33sofT', enquireLinkTimerSecs=120, responseTimerSecs=300, )
    SMPP(smpp_config, db_config, logger).run()
    reactor.run()
