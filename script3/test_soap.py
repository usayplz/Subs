#!/usr/bin/env python
# -*- coding: utf-8 -*-

from suds.client import Client
from suds.transport.http import HttpAuthenticated
from suds.cache import DocumentCache
from suds import WebFault
import os, datetime, logging, sys


from suds.plugin import *
class NamespaceCorrectionPlugin(MessagePlugin):
    def received(self, context):
        context.reply = context.reply.replace('"http://namespaces.soaplite.com/perl"','"API"')


class RTSoapClient(object):

    def __init__(self, credentials):
        soap_url = 'http://95.85.31.41/rtsoapservice/?service'
        wsdl_url = 'http://95.85.31.41/rtsoapservice/?service.wsdl'

        t = HttpAuthenticated(**credentials)
        self.api = Client(url=wsdl_url, location=soap_url, transport=t, plugins = [NamespaceCorrectionPlugin()])
        # self.api.options.transport.urlopener  = urllib2.build_opener(authhandler)

        # self.api.set_options(cache=DocumentCache())

    def request(self, method_name, params):
        # try:
        result = self.api.service['RTSoapApp'][method_name](params)
        return result
        # except WebFault, err:
        #     # self.logger.info(unicode(err))
        #     pass
        #     print unicode(err)
        # except:
        #     pass
        #     # self.logger.info('Other error: ' + str(sys.exc_info()[1]))
        #     print str(sys.exc_info()[0])
        return -1


if __name__ == '__main__':  
    import logging
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('suds.client').setLevel(logging.DEBUG)
    # logging.getLogger('suds.client').setLevel(logging.DEBUG)

    client = RTSoapClient(dict(username='rtamstudio', password='J(*Dewfhu3)'))
    params = {
        'contractID': 1,
        'unitID': 1,
        'userNumber': '79021702030',
        'mode': 3,
        'price': 2.2,
        'capabilities': {
            'model': '',
            'profile': '',
            'uagent': '',
            'accept': '',
            'weight': 33,
            'height': 44,
        },
        'parameters': '3',
        'regionID': '4',
    }


    # print client.request('createContract', params)
    params = {
        'contractID': 0,
        'state': 1,
        'parameters': '2',
    }
    # print client.api#.service.createContract(params)
    print client.api.service.registerError(1,1,'test')
    # print result
    # print client.request('registerError', params)
    # print client.api.service.registerError(1,1,'meess')
    sys.exit(1)

    

