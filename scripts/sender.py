#!/usr/bin/env python

import logging
from twisted.internet import reactor, defer
from smpp.twisted.client import SMPPClientTransceiver, SMPPClientService
from smpp.twisted.config import SMPPClientConfig
from smpp.pdu.error import *
from smpp.pdu.operations import *
from smpp.pdu.pdu_types import *


class SMPP(object):
    sme_num = '8181'

    def __init__(self, config=None):
        if config is None:
            config = SMPPClientConfig(host='81.18.113.146', port=3202, username='272', 
            	password='Ha33sofT', )
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
        print "Received pdu: %s" % pdu
        print "DEBUG :: %s" % pdu.commandId

        if pdu.commandId == CommandId.deliver_sm:
            submit_pdu = SubmitSM(
                source_addr=self.sme_num,
                destination_addr=pdu.params['source_addr'],
                short_message='HELLO',
                source_addr_ton=AddrTon.ALPHANUMERIC,
                dest_addr_ton=AddrTon.INTERNATIONAL,
                dest_addr_npi=AddrNpi.ISDN,
            )
            smpp.sendDataRequest(submit_pdu)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    SMPP().run()
    reactor.run()