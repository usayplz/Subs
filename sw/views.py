# -*- coding: utf-8 -*-

from django.shortcuts import render
from sw.models import WeatherText
from datetime import datetime

def index(request):
    weathers = WeatherText.objects.filter(time_from__lte=datetime.now(), time_to__gte=datetime.now())
    return render(request, 'sw/index.html', {"weathers": weathers})

def wsdl(request):
    return render(request, 'sw/rt.wsdl', {}, content_type='application/xhtml+xml')
