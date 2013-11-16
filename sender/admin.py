# -*- coding: utf-8 -*-
from django.contrib import admin
from sender.models import Mailing, Subscriber, SMSTask
from django.forms import CheckboxSelectMultiple
from django.db import models


class MailingAdmin(admin.ModelAdmin):
    exclude = ('create_user',)
    list_display = ('name', 'bwc_location_code', 'weather_location_code', 'create_date', 'create_user',)
    list_filter = ('create_user',)
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
    list_filter = ('mailing', 'status', 'create_date',)
    class Meta:
        model = Subscriber


class SMSTaskAdmin(admin.ModelAdmin):
    list_display = ('delivery_date', 'mobnum', 'status', 'in_text', 'out_text', 'sent_date',)
    list_filter = ('status', 'delivery_date',)
    class Meta:
        model = SMSTask


admin.site.register(Mailing, MailingAdmin)
admin.site.register(Subscriber, SubscriberAdmin)
admin.site.register(SMSTask, SMSTaskAdmin)
