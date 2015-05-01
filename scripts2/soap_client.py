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
        # self.logger = logger
        soap_url = 'http://api.rostelecontent.ru/server.services.php'
        wsdl_url = 'http://api.rostelecontent.ru/services.wsdl'

        transport = HttpAuthenticated(**credentials)

        self.api = Client(url=wsdl_url, location=soap_url, transport=transport, plugins = [NamespaceCorrectionPlugin()])
        self.api.set_options(cache=DocumentCache())

    def request(self, method_name, params):
        try:
            result = self.api.service['servicesPort'][method_name](params)
            return result
        except WebFault, err:
            # self.logger.info(unicode(err))
            #print unicode(err)
            pass
        except:
            pass
            #print str(sys.exc_info()[1])
            # self.logger.info('Other error: ' + str(sys.exc_info()[1]))
        return -1


if __name__ == '__main__':    
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('suds.client').setLevel(logging.DEBUG)

    client = RTSoapClient(dict(username='amstudio', password='JHMaNf5S'))

    folders = {
        'folder': {
            'folderID': 1,
            'parentID': 0,
            'name': 'Smart Weather',
            'deleted': False,
            'adult': False,
            'index': 0,
        },
    }
    # print client.api.service.updateFolder(folders)

    units = {
        'unit': {
            'unitID': 1,
            'parentID': 1,
            'kind': 221, # Ежедневная подписка
            'name': 'daily',
            # 'author' 'amstudio',
            # 'brief': '',
            # 'info': '',
            # 'imageURL': '',
            # 'previewURL': '',
            # 'tags': '',
            # 'important': False,
            # 'pack': '',
            # 'index': 0,
            'price': 2,
            # 'serviceType': 1,
            'period': 3,
            # 'trial': 0,
            # 'creditPeriod': 10,
            # 'duration': 3000,
            # 'sendingTime': '19:30',
            # 'weekDays': '+++++++',
            # 'onum': '418',
            # 'code': 'weather',
            # 'conditions': '',
            'mode': 1,
            # 'models': '',
            # 'parameters': '',
        },
    }
    #print client.api.service.updateUnit(units)

    contract = {
        'requestID': 2,
        'userNumber': '7901702030',
        'unitID': 1,
        'mode': 1,
        'price': 2,
        # 'parameters': '',
        'reason': {
            'type': 2,
            'number': '4181', 
        },
    }
    # Type
        # 0= импорт существующих контрактов 
        # 1= SMS-запрос абонента
        # 2= USSD-запрос абонента
        # 3= WAP-запрос абонента
        # 5= Предыдущий контракт
        # 6= IVR-запрос абонента
        # 7= Заполненная письменная форма 8 = Pin код
    # print client.request('requestContract', contract)
    #print client.api.service.requestContract(6, '79025114117', 1, 1, 2, '', { 'type': 1, 'number': '4181', 'message': '414', })

    contracts = {
        'contractID': 60346,
        'state': 1, # 1=Контракт продолжается. 2=Контракт прекращается. 3=Контракт заблокирован.
        # 'price': 2,
        # 'parameters': '',
        # 'reason': '',
    }
    # print client.request('modifyContract', units)
    #print client.api.service.modifyContract(59501, 2, 2, '', { 'type': 2, 'number': '4181', 'message': 'stop', })
    #print client.api.service.contractState(60349)
    print client.request('contractState', { "contractID": 61798 })
