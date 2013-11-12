#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, logging, datetime
from twisted.internet import reactor, defer, task
from smpp.twisted.client import SMPPClientTransceiver, SMPPClientService
from smpp.twisted.config import SMPPClientConfig
from twisted.python import failure
from smpp.pdu.operations import *
from smpp.pdu.pdu_types import *
import dbsmstask, pid


class SMPP(object):
    ESME_NUM = '*8181#'
    SOURCE_ADDR_TON = AddrTon.UNKNOWN
    SOURCE_ADDR_NPI = AddrNpi.ISDN
    DEST_ADDR_TON = AddrTon.INTERNATIONAL
    DEST_ADDR_NPI = AddrNpi.ISDN
    MENU = {
        u'*8181#': u'1.Погода в моем городе 2.Погода в других городах 3.Отписаться 0.Мои подписки',
        u'2': u'1. Иркутск\n2. Ангарск\n3. Братск\n4. Байкальск\n5. Улан-Удэ\n6. Аршан',
        u'3': u'Вы отписаны от рассылки',
        u'0': u'Мои подписки',
    }

    def __init__(self, smpp_config, db_config, logger):
        self.smpp_config = smpp_config
        self.db_config = db_config
        self.logger = logger
        self.smstask = dbsmstask.dbSMSTask(db_config, logger)

    @defer.inlineCallbacks
    def run(self):
        try:
            self.smpp = yield SMPPClientTransceiver(self.smpp_config, self.handleMsg).connectAndBind()
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

                # self.logger.info('current my_num = %s' % my_num)
                # if my_num in ['*8181*2#']:
                    # self.send_ussd(smpp, my_num, source_addr, u'1. Иркутск\n2. Ангарск\n3. Братск\n4. Байкальск\n5. Улан-Удэ\n6. Аршан')
                # elif my_num in ['*8181*3#']:
                    # self.smstask.unsubscribe(source_addr)
                    # self.send_ussd(smpp, my_num, source_addr, u'Вы отписаны от всех рассылок.')
                # elif my_num in ['*8181*2*1#','*8181*2*2#','*8181*2*3#','*8181*2*4#','*8181*2*5#','*8181*2*6#']:
                    # self.smstask.subscribe(source_addr, u'2%s' % short_message)
                    # self.send_ussd(smpp, my_num, source_addr, u'Вы подписаны на рассылку.')
                # else:
                    # my_num = self.ESME_NUM
                    # self.send_ussd(smpp, my_num, source_addr, u'1.Погода в моем городе\n2.Другие города\n3.Отписаться\n0.Мои подписки')
                #     # task_id = self.smstask.add_new_task(source_addr, short_message)
                #     self.logger.info('new task (id, mobnum, text): %s, %s, %s' % (task_id, source_addr, self.smstask.weather))
                #     # self.smstask.subscribe(source_addr)

    def send_ussd(self, smpp, my_num, source_addr, short_message):
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
            ussd_service_op=ussdServiceOp.USSR_REQUEST,
        )
        return smpp.sendDataRequest(submit_pdu)

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
    log_file = os.path.join(os.path.dirname(__file__), 'log', '%s_%s' % (datetime.date.today().strftime('%d%m%Y'), 'ussd.log'))
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)-15s %(levelname)s %(message)s",
        filename=log_file
    )
    logger = logging.getLogger(__name__)
    logger.critical = critical

    # start
    logger.info('[START PROGRAM]')
    db_config = {'host': 'localhost', 'user': 'subs', 'passwd': 'njH(*DHWH2)', 'db': 'subsdb'}
    smpp_config = SMPPClientConfig(
        host='81.18.113.146', port=3204, username='amstudio', password='Yrj39sVa', enquireLinkTimerSecs=60, )
    SMPP(smpp_config, db_config, logger).run()
    reactor.run()
