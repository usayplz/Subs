# -*- coding: utf-8 -*-

from django.shortcuts import render

def wsdl(request):
    return render(request, 'sw/rt.wsdl', {}, content_type='application/xhtml+xml')
