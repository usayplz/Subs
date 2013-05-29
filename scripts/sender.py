#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from twisted.internet import reactor, defer, task
from smpp.twisted.client import SMPPClientTransceiver, SMPPClientService
from smpp.twisted.config import SMPPClientConfig
from smpp.pdu.operations import *
from smpp.pdu.pdu_types import *
import dbsmstask


class SMPP(object):
    ESME_NUM = '8181'
    SOURCE_ADDR_TON = AddrTon.ALPHANUMERIC
    DEST_ADDR_TON = AddrTon.INTERNATIONAL
    DEST_ADDR_NPI = AddrNpi.ISDN

    def __init__(self, smpp_config=None, db_config=None):
        self.smpp_config = smpp_config
        self.db_config = db_config
        self.smstask = dbsmstask.dbSMSTask(db_config)

    @defer.inlineCallbacks
    def run(self):
        try:
            self.smpp = yield SMPPClientTransceiver(self.smpp_config, self.handleMsg).connectAndBind()
            self.lc_send_all = task.LoopingCall(self.send_all)
            self.lc_send_all.start(60)
            yield self.smpp.getDisconnectedDeferred()
        except Exception, e:
            print "ERROR: %s" % str(e)
        finally:
            reactor.stop()

    def handleMsg(self, smpp, pdu):
        source_addr = pdu.params.get('source_addr', '')
        short_message = pdu.params.get('short_message', '')
        message_state = pdu.params.get('message_state', None)

        if pdu.commandId == CommandId.deliver_sm:
            if message_state == MessageState.DELIVERED:
                pass
            else:
                short_message = short_message.decode('utf_16_be')
                self.smstask.add_new_task(source_addr, pdu.seqNum)
                d = self.send_sms(smpp, source_addr, self.smstask.weather)
                d.addBoth(self.message_sent)

    def send_sms(self, smpp, source_addr, short_message):
        """params:
            report: on
            encoding: UCS2
        """
        short_message = short_message.encode('utf_16_be')

        submit_pdu = SubmitSM(
            source_addr=self.ESME_NUM,
            destination_addr=source_addr,
            short_message=short_message,
            source_addr_ton=self.SOURCE_ADDR_TON,
            dest_addr_ton=self.DEST_ADDR_TON,
            dest_addr_npi=self.DEST_ADDR_NPI,
            esm_class=EsmClass(EsmClassMode.DEFAULT, EsmClassType.DEFAULT),
            protocol_id=0,
            registered_delivery=RegisteredDelivery(
                RegisteredDeliveryReceipt.SMSC_DELIVERY_RECEIPT_REQUESTED),
            replace_if_present_flag=ReplaceIfPresentFlag.DO_NOT_REPLACE,
            data_coding=DataCoding(DataCodingScheme.DEFAULT, DataCodingDefault.UCS2),
        )
        return smpp.sendDataRequest(submit_pdu)

    def message_sent(self, *args, **kwargs):
        print self
        for arg in args:
            print "ARG:", arg

        for key in kwargs:
            print "another keyword ARG: %s: %s" % (key, kwargs[key])
        #if self.error:
        #    self.smstask.update_task_status(1, task_id, message_id)
        #else:
        #    self.smstask.update_task_status(4, task_id, message_id)

    def send_all(self):
        print "send_all"
        tasks = self.smstask.check_tasks()
        for task in tasks:
            task_id, mobnum, sms_text = task
            d = self.send_sms(self.smpp, mobnum, sms_text)
            d.addBoth(self.message_sent, task_id)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    db_config = {'host': 'localhost', 'user': 'subs', 'passwd': 'njH(*DHWH2)', 'db': 'subsdb'}
    smpp_config = SMPPClientConfig(
        host='81.18.113.146', port=3202, username='272', password='Ha33sofT', enquireLinkTimerSecs=60, )
    SMPP(smpp_config, db_config).run()
    reactor.run()
