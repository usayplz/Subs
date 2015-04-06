# -*- coding: utf-8 -*-

from django.shortcuts import render
from datetime import datetime
from models import WeatherText


def index(request):
    current_weather = WeatherText.objects.filter(time_from__lt=datetime.now, time_to__gt=datetime.now)
    return render(request, 'sender/index.html', {'current_weather': current_weather})
