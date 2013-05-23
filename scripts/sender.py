#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from twisted.internet import reactor, defer
from smpp.twisted.client import SMPPClientTransceiver, SMPPClientService
from smpp.twisted.config import SMPPClientConfig
from smpp.pdu.error import *
from smpp.pdu.operations import *
from smpp.pdu.pdu_types import *


class SMPP(object):
    esme_num = '8181'
    source_addr_ton = AddrTon.ALPHANUMERIC
    dest_addr_ton = AddrTon.INTERNATIONAL
    dest_addr_npi = AddrNpi.ISDN

    def __init__(self, config=None):
        if config is None:
            config = SMPPClientConfig(
                host='81.18.113.146', port=3202, username='272', password='Ha33sofT', enquireLinkTimerSecs=60, )
        self.config = config

    @defer.inlineCallbacks
    def run(self):
        try:
            smpp = yield SMPPClientTransceiver(self.config, self.handleMsg).connectAndBind()
            yield smpp.getDisconnectedDeferred()
        except Exception, e:
            print "ERROR: %s" % str(e)
        finally:
            reactor.stop()

    def handleMsg(self, smpp, pdu):
        #print "Received pdu: %s" % pdu

        # some variables
        source_addr = pdu.params.get('source_addr', '')
        short_message = pdu.params.get('short_message', '')
        message_state = pdu.params.get('message_state', None)

        if pdu.commandId == CommandId.deliver_sm:
            if message_state == MessageState.DELIVERED:
                print "=============DEBUG============ %s" % message_state
            else:
                short_message = short_message.decode('utf_16_be')
                seq = self.send_sms(smpp, source_addr, u'цук')
                print "=============DEBUG============ seq=%s" % seq
                # add2db


    def send_sms(self, smpp, source_addr, short_message):
        """params:
            report: on
            encoding: UCS2
        """
        short_message = short_message.encode('utf_16_be')

        submit_pdu = SubmitSM(
            source_addr=self.esme_num,
            destination_addr=source_addr,
            short_message=short_message,
            source_addr_ton=self.source_addr_ton,
            dest_addr_ton=self.dest_addr_ton,
            dest_addr_npi=self.dest_addr_npi,
            esm_class=EsmClass(EsmClassMode.DEFAULT, EsmClassType.DEFAULT),
            protocol_id=0,
            registered_delivery=RegisteredDelivery(
                RegisteredDeliveryReceipt.SMSC_DELIVERY_RECEIPT_REQUESTED),
            replace_if_present_flag=ReplaceIfPresentFlag.DO_NOT_REPLACE,
            data_coding=DataCoding(DataCodingScheme.DEFAULT, DataCodingDefault.UCS2),
        )
        return smpp.sendDataRequest(submit_pdu)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    SMPP().run()
    reactor.run()
