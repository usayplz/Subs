# -*- coding: utf-8 -*-
from django.contrib import admin
from sw.models import Mailing, Subscriber, SMSTask, WeatherText, SMSTaskLog
from django.forms import CheckboxSelectMultiple
from django.db import models


def yarno_url(obj):
    if obj.yrno_location_code:
        return u'<a target="_blank" href="http://www.yr.no/place/%s">%s</a>' % (obj.yrno_location_code, obj.yrno_location_code)
    return obj.yrno_location_code
yarno_url.short_description = u'Идентификатор города yr.no'
yarno_url.allow_tags = True


class MailingAdmin(admin.ModelAdmin):
    list_display = ('name', yarno_url, 'create_date',)
    list_filter = ('name',)
    search_fields = ['name', yarno_url]
    list_per_page = 1000
    formfield_overrides = {
        models.ManyToManyField: {'widget': CheckboxSelectMultiple},
    }

    class Meta:
        model = Mailing


class SubscriberAdmin(admin.ModelAdmin):
    list_display = ('mobnum', 'mailing', 'status', 'create_date', 'subs_time', 'request_id', 'contract_id', 'contract_state',)
    list_filter = ('status', 'create_date',)
    search_fields = ['mobnum', 'request_id', 'contract_id', 'contract_state']
    class Meta:
        model = Subscriber


class SMSTaskAdmin(admin.ModelAdmin):
    list_display = ('delivery_date', 'mobnum', 'status', 'in_text', 'out_text', 'sent_date',)
    list_filter = ('status', 'delivery_date',)
    search_fields = ['mobnum', 'in_text', 'out_text']
    list_per_page = 1000
    class Meta:
        model = SMSTask


class SMSTaskLogAdmin(admin.ModelAdmin):
    list_display = ('delivery_date', 'mobnum', 'status', 'in_text', 'out_text', 'sent_date',)
    list_filter = ('status', 'delivery_date',)
    search_fields = ['mobnum', 'in_text', 'out_text']
    list_per_page = 1000
    class Meta:
        model = SMSTaskLog


class WeatherTextAdmin(admin.ModelAdmin):
    list_display = ('mailing', 'create_date', 'text', 'temperature', 'wcondition', 'wind_direction', 'wind_speed', 'pressure', 'time_from', 'time_to', )
    list_filter = ('time_from', 'time_to', 'create_date',)
    search_fields = ['text']
    list_per_page = 1000
    class Meta:
        model = WeatherText


admin.site.register(Mailing, MailingAdmin)
admin.site.register(Subscriber, SubscriberAdmin)
admin.site.register(SMSTask, SMSTaskAdmin)
admin.site.register(SMSTaskLog, SMSTaskLogAdmin)
admin.site.register(WeatherText, WeatherTextAdmin)

