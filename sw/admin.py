# -*- coding: utf-8 -*-
from django.contrib import admin
from sw.models import Mailing, Subscriber, SMSTask, WeatherText, SMSTaskLog, LastPayment
from django.forms import CheckboxSelectMultiple
from django.db import models
from django import forms
from django.contrib.admin.helpers import ActionForm
from daterange_filter.filter import DateRangeFilter
import sys
from django.conf import settings

sys.path.append('/var/www/subs/scripts/')
import dbsmstask


def yarno_url(obj):
    if obj.yrno_location_code:
        return u'<a target="_blank" href="http://www.yr.no/place/%s">%s</a>' % (obj.yrno_location_code, obj.yrno_location_code)
    return obj.yrno_location_code
yarno_url.short_description = u'Идентификатор города yr.no'
yarno_url.allow_tags = True


class MailingAdmin(admin.ModelAdmin):
    list_display = ('name', yarno_url, 'timezone', 'create_date',)
    list_filter = ('name',)
    search_fields = ['name', yarno_url]
    list_per_page = 1000
    formfield_overrides = {
        models.ManyToManyField: {'widget': CheckboxSelectMultiple},
    }

    class Meta:
        model = Mailing


# SUBSCRIBERS
class SubscribeActionForm(ActionForm):
    phone = forms.CharField(label=u'Номер телефона (11 знаков): ', max_length=11, required=False)
    mailing = forms.ModelChoiceField(label=u'Рассылка', queryset=Mailing.objects.all(), required=False)

class SubscriberAdmin(admin.ModelAdmin):
    list_display = ('mobnum', 'mailing', 'status', 'create_date', 'subs_time', 'request_id', 'contract_id', 'contract_state',)
    list_filter = ('status', 'create_date', 'contract_state',)
    search_fields = ['mobnum', 'request_id', 'contract_id', 'contract_state']
    action_form = SubscribeActionForm
    actions = ['adction_unsubscribe', 'action_subscribe']
    class Meta:
        model = Subscriber

    def changelist_view(self, request, extra_context=None):
        if 'action' in request.POST and request.POST['action'] == 'action_subscribe':
            if not request.POST.getlist(admin.ACTION_CHECKBOX_NAME):
                post = request.POST.copy()
                for u in Subscriber.objects.all():
                    post.update({admin.ACTION_CHECKBOX_NAME: str(u.id)})
                    break
                request._set_post(post)
        return super(SubscriberAdmin, self).changelist_view(request, extra_context)

    def action_subscribe(self, request, queryset):
        phone = request.POST['phone']
        mailing = request.POST['mailing']
        if phone and mailing:
            tasker = dbsmstask.dbSMSTask(settings.DATABASES['default'], None)
            tasker.subscribe(phone, mailing, 'SMS', '4181')
    action_subscribe.short_description = u'Подписать'

    def adction_unsubscribe(self, request, queryset):
        for qs in queryset:
            print qs.mobnum
            # tasker = dbsmstask.dbSMSTask(settings.DATABASES['default'], None)
            # tasker.unsubscribe(qs.mobnum)
    adction_unsubscribe.short_description = u'Отписать'

# END OF SUBSCRIBERS

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


class LastPaymentAdmin(admin.ModelAdmin):
    list_display = ('mobnum', 'payment_date',)
    list_filter = (
        ('payment_date', DateRangeFilter), # this is a tuple
    )
    search_fields = ['mobnum']
    list_per_page = 100
    class Meta:
        model = LastPayment


admin.site.register(Mailing, MailingAdmin)
admin.site.register(Subscriber, SubscriberAdmin)
admin.site.register(SMSTask, SMSTaskAdmin)
admin.site.register(SMSTaskLog, SMSTaskLogAdmin)
admin.site.register(WeatherText, WeatherTextAdmin)
admin.site.register(LastPayment, LastPaymentAdmin)

