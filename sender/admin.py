# -*- coding: utf-8 -*-
from django.contrib import admin
from sender.models import MailingCron, Mailing, Subscriber, SMSTask, SMSText, MailingNumber
from django.forms import CheckboxSelectMultiple
from django.db import models


class MailingCronAdmin(admin.ModelAdmin):
    class Meta:
        model = MailingCron


class MailingAdmin(admin.ModelAdmin):
    exclude = ('create_user',)
    list_display = ('code', 'name', 'location', 'create_date', 'create_user')
    formfield_overrides = {
        models.ManyToManyField: {'widget': CheckboxSelectMultiple},
    }

    def save_model(self, request, obj, form, change):
        obj.create_user = request.user
        obj.save()

    class Meta:
        model = Mailing


class SubscriberAdmin(admin.ModelAdmin):
    list_display = ('mobnum', 'mailing', 'create_date')
    list_filter = ('mailing', 'create_date')
    class Meta:
        model = Subscriber


class SMSTaskAdmin(admin.ModelAdmin):
    list_display = ('delivery_date', 'mobnum', 'status', 'in_text', 'out_text', 'sent_date')
    list_filter = ('status', 'delivery_date')
    class Meta:
        model = SMSTask


class SMSTextAdmin(admin.ModelAdmin):
    list_display = ('sms_text', 'mailing', 'from_date', 'to_date')
    list_filter = ('mailing', 'from_date', 'to_date')

    class Meta:
        model = SMSText

class MailingNumberAdmin(admin.ModelAdmin):
    exclude = ('create_user',)
    list_filter = ('mailing', 'number_from', 'number_to', 'create_date', 'create_user')
    list_display = ('mailing', 'number_from', 'number_to', 'create_date', 'create_user')
    
    def save_model(self, request, obj, form, change):
        obj.create_user = request.user
        obj.save()

    class Meta:
        model = MailingNumber

admin.site.register(MailingCron, MailingCronAdmin)
admin.site.register(Mailing, MailingAdmin)
admin.site.register(Subscriber, SubscriberAdmin)
admin.site.register(SMSTask, SMSTaskAdmin)
admin.site.register(SMSText, SMSTextAdmin)
admin.site.register(MailingNumber, MailingNumberAdmin)
