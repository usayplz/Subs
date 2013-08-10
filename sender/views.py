# -*- coding: utf-8 -*-
from django.shortcuts import render
from sender.models import SMSText
from datetime import datetime


def index(request):
    current_weather = SMSText.objects.filter(from_date__lt=datetime.now, to_date__gt=datetime.now)
    return render(request, 'sender/index.html', {'current_weather': current_weather})
