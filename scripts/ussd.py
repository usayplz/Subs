#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, logging, datetime
from twisted.internet import reactor, defer, task
from smpp.twisted.client import SMPPClientTransceiver, SMPPClientService
from smpp.twisted.config import SMPPClientConfig
from twisted.python import failure
from smpp.pdu.operations import *
from smpp.pdu.pdu_types import *
import dbsmstask, pid

# db config
sys.path.append('/var/www/subs/')
from local_settings import DATABASES


class SMPP(object):
    ESME_NUM = '*8181#'
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
            self.lc_refresh_dbconnect = task.LoopingCall(self.refresh_dbconnect)
            self.lc_refresh_dbconnect.start(180)
            yield self.smpp.getDisconnectedDeferred()
        except Exception, e:
            self.logger.critical(e)
            raise
        finally:
            reactor.stop()

    def handleMsg(self, smpp, pdu):
        self.logger.info('PDU = %s' % pdu)

        dest_addr = pdu.params.get('destination_addr', '')
        source_addr = pdu.params.get('source_addr', '')
        short_message = pdu.params.get('short_message', '').strip()
        message_state = pdu.params.get('message_state', None)
        message_id = pdu.params.get('receipted_message_id', -1)
        data_coding = pdu.params.get('data_coding', '')
        ussd_service = pdu.params.get('ussd_service_op', '')

        if pdu.commandId == CommandId.deliver_sm:
            if message_state is None:
                if ussd_service == ussdServiceOp.USSR_CONFIRM:
                    my_num = '%s*%s#' % (dest_addr[:-1], short_message)
                else:
                    my_num = dest_addr

                self.logger.info('current my_num = %s' % my_num)
                (mailing_id, weather) = self.smstask.get_current_weather(source_addr, 1)

                # set time
                if len(short_message) > 6:
                    set_time_result = self.smstask.set_time(source_addr, short_message, mailing_id)
                    if set_time_result != '':
                        sms_text = u'Вы сменили время рассылки погоды на %s' % set_time_result[0:5]
                    else:
                        sms_text = u'Неверный формат времени. Пример установки на 19:30 - *818*1930#'
                    self.send_ussd(smpp, my_num, source_addr, sms_text, ussdServiceOp.USSN_REQUEST)
                    self.logger.info('Set time (mobnum, text): %s, %s' % (source_addr, text))
                    task_id = self.smstask.add_new_task(source_addr, short_message, sms_text, 1)
                    if weather != '':
                        self.smstask.subscribe(source_addr, mailing_id)
                    return
                
                # if my_num in '*818#' or my_num in '*8181#':
                self.logger.info('mailing_id = %s' % mailing_id)
                if weather:
                    self.send_ussd(smpp, my_num, source_addr, weather, ussdServiceOp.USSN_REQUEST)
                    task_id = self.smstask.add_new_task(source_addr, short_message, weather, 1)
                    self.smstask.subscribe(source_addr, mailing_id)
                    self.logger.info('new task (id, mobnum, text): %s, %s, %s' % (task_id, source_addr, weather))
                elif mailing_id:
                    sms_text = u'Для Вашего нас. пункта нет погоды.'
                    self.send_ussd(smpp, my_num, source_addr, sms_text, ussdServiceOp.USSN_REQUEST)
                    self.logger.info('ERROR: cannot get weather (mobnum, text): %s, %s' % (source_addr, weather))
                    task_id = self.smstask.add_new_task(source_addr, short_message, sms_text, 1)
                else:
                    sms_text = u'Нас. пункт не определен. Отправьте смс с названием на 8181.'
                    self.send_ussd(smpp, my_num, source_addr, sms_text, ussdServiceOp.USSN_REQUEST)
                    self.logger.info('ERROR: cannot get city (mobnum, text): %s, %s' % (source_addr, weather))
                    task_id = self.smstask.add_new_task(source_addr, short_message, sms_text, 1)

    def send_ussd(self, smpp, my_num, source_addr, short_message, _ussd_service_op):
        short_message = short_message.encode('utf_16_be')

        submit_pdu = SubmitSM(
            service_type='USSD',
            source_addr=my_num,
            destination_addr=source_addr,
            short_message=short_message,
            source_addr_ton=self.SOURCE_ADDR_TON,
            source_addr_npi=self.SOURCE_ADDR_NPI,
            dest_addr_ton=self.DEST_ADDR_TON,
            dest_addr_npi=self.DEST_ADDR_NPI,
            esm_class=EsmClass(EsmClassMode.DEFAULT, EsmClassType.DEFAULT),
            data_coding=DataCoding(DataCodingScheme.DEFAULT, DataCodingDefault.UCS2), #SMS_DEFAULT_ALPHABET),
            ussd_service_op=_ussd_service_op,
        )
        return smpp.sendDataRequest(submit_pdu)

    def refresh_dbconnect(self):
        tasks = self.smstask.check_tasks()


def critical(msg, *args, **kwargs):
    logger.error(msg)
    reactor.stop()


if __name__ == '__main__':
    # check pid
    PID = 'ussd.pid'
    if pid.check_pid(int(pid.read_pid(PID))):
        print "Already running %s" % (PID,)
        exit(0)
    else:
        pid.write_pid(PID)

    # logger
    log_file = os.path.join(os.path.dirname(__file__), 'logs', '%s_%s' % (datetime.date.today().strftime('%d%m%Y'), 'ussd.log'))
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
        host='81.18.113.146', port=3204, username='amstudio', password='Yrj39sVa', enquireLinkTimerSecs=120, )
    SMPP(smpp_config, db_config, logger).run()
    reactor.run()
