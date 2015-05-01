#!/usr/bin/env python
# -*- coding: utf-8 -*-

from suds.client import Client
from suds.transport.http import HttpAuthenticated
from suds.cache import DocumentCache
from suds import WebFault
import os, datetime, logging, sys
import logging


from suds.plugin import *
class NamespaceCorrectionPlugin(MessagePlugin):
    def received(self, context):
        context.reply = context.reply.replace('"http://namespaces.soaplite.com/perl"','"API"')


class RTSoapClient(object):
    def __init__(self, credentials):
        # logging.basicConfig(level=logging.INFO)
        # logging.getLogger('suds.client').setLevel(logging.DEBUG)

        soap_url = 'http://api.rostelecontent.ru/server.services.php'
        wsdl_url = 'http://api.rostelecontent.ru/services.wsdl'

        transport = HttpAuthenticated(**credentials)

        self.api = Client(url=wsdl_url, location=soap_url, transport=transport, plugins = [NamespaceCorrectionPlugin()])
        self.api.set_options(cache=None)

    def request(self, method_name, params):
        try:
            return self.api.service['servicesPort'][method_name](params)
        except WebFault, err:
            # print unicode(err)
            return -1
        except:
            # print 'Other error: ' + str(sys.exc_info()[1])
            return -1


if __name__ == '__main__':
    a = (u'Город %s привет' % (u'hi'))[0:10]
    print a
    sys.exit()

    client = RTSoapClient(dict(username='amstudio', password='JHMaNf5S'))
    # result = client.api.service.requestContract(8, '79021702030', 1, 1, 2, '', { 'type': 1, 'number': '4181', 'message': '414', })
    # print result.status
    # 1=Контракт продолжается. 2=Контракт прекращается. 3=Контракт заблокирован.
    # print client.api.service.modifyContract(60349, 2, 2, '', { 'type': 2, 'number': '4181', 'message': 'stop', })
    #print client.api.service.contractState(60349)
    # print client.request('contractState', { "contractID": 60349 })

