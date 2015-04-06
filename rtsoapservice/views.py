# -*- coding: utf-8 -*-

from django.shortcuts import render

from soaplib.serializers.primitive import Boolean, String, Integer, Decimal
from soaplib.serializers.clazz import ClassSerializer
from soaplib.service import DefinitionBase, rpc
from rtsoap import RTSoapApp

class Capabilites(ClassSerializer):
    model = String
    profile = String
    uagent = String
    accept = String
    weight = Integer
    height = Integer

class CreateContractAnswer(ClassSerializer):
    status = Integer
    url = String
    hash = String
    message = String

class RTSOAPService(DefinitionBase):
    @rpc(Integer, Integer, String, Integer, Decimal, Capabilites, String, Integer, _returns=CreateContractAnswer)
    def createContract(self, contractID, unitID, userNumber, mode, price, capabilities, parameters, regionID):
        from sender.models import SMSTask
        task = SMSTask()
        task.mobnum = '97021702030'
        task.in_text = str(unitID)
        task.out_text = str(contractID)
        status = 2
        task.save()
        return CreateContractAnswer(0, '', '', '')

    @rpc(Integer, Integer, String)
    def updateContract (self, contractID, state, parameters):
        from sender.models import SMSTask
        task = SMSTask()
        task.mobnum = '98021702030'
        task.in_text = str(state)
        task.out_text = str(contractID)
        status = 2
        task.save()
        return

    @rpc(Integer, Integer, String)
    def registerError(self, code, id, message):
        from sender.models import SMSTask
        task = SMSTask()
        task.mobnum = '99021702030'
        task.in_text = 'registerError'
        task.out_text = message
        status = 2
        task.save()
        return

# the view to use in urls.py
rt_soap_service = RTSoapApp([RTSOAPService], __name__)
