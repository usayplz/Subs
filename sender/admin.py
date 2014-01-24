# -*- coding: utf-8 -*-
from django.contrib import admin
from sender.models import Mailing, Subscriber, SMSTask, WeatherText
from django.forms import CheckboxSelectMultiple
from django.db import models


def yarno_url(obj):
    if obj.yrno_location_code:
        return u'<a target="_blank" href="http://www.yr.no/place/%s">%s</a>' % (obj.yrno_location_code, obj.yrno_location_code)
    return obj.yrno_location_code
yarno_url.short_description = u'Идентификатор города yr.no'
yarno_url.allow_tags = True

class MailingAdmin(admin.ModelAdmin):
    exclude = ('create_user',)
    list_display = ('name', 'bwc_location_code', 'weather_location_code', yarno_url, 'create_date', 'create_user',)
    list_filter = ('create_user',)
    search_fields = ['name', 'bwc_location_code', 'weather_location_code']
    list_per_page = 1000
    formfield_overrides = {
        models.ManyToManyField: {'widget': CheckboxSelectMultiple},
    }

    def save_model(self, request, obj, form, change):
        obj.create_user = request.user
        obj.save()

    class Meta:
        model = Mailing


class SubscriberAdmin(admin.ModelAdmin):
    list_display = ('mobnum', 'mailing', 'status', 'create_date',)
    list_filter = ('status', 'create_date',)
    search_fields = ['mobnum']
    class Meta:
        model = Subscriber


class SMSTaskAdmin(admin.ModelAdmin):
    list_display = ('delivery_date', 'mobnum', 'status', 'in_text', 'out_text', 'sent_date',)
    list_filter = ('status', 'delivery_date',)
    search_fields = ['mobnum', 'in_text', 'out_text']
    list_per_page = 1000
    class Meta:
        model = SMSTask


class WeatherTextAdmin(admin.ModelAdmin):
    list_display = ('mailing', 'create_date', 'text', 'temperature', 'wcondition', 'wind_direction', 'wind_speed', 'time_from', 'time_to', )
    list_filter = ('time_from', 'time_to', 'create_date',)
    search_fields = ['text']
    list_per_page = 1000
    class Meta:
        model = WeatherText


admin.site.register(Mailing, MailingAdmin)
admin.site.register(Subscriber, SubscriberAdmin)
admin.site.register(SMSTask, SMSTaskAdmin)
admin.site.register(WeatherText, WeatherTextAdmin)
