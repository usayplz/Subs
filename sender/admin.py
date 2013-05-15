# -*- coding: utf-8 -*-
from django.contrib import admin
from sender.models import MailingCron, Mailing, Subscriber, SMSTask, SMSText


class MailingCronAdmin(admin.ModelAdmin):
    class Meta:
        model = MailingCron


class MailingAdmin(admin.ModelAdmin):
    exclude = ('create_user',)
    
    def save_model(self, request, obj, form, change):
        obj.create_user = request.user
        obj.save()

    class Meta:
        model = Mailing


class SubscriberAdmin(admin.ModelAdmin):
    class Meta:
        model = Subscriber


class SMSTaskAdmin(admin.ModelAdmin):
    class Meta:
        model = SMSTask


class SMSTextAdmin(admin.ModelAdmin):
    class Meta:
        model = SMSText


admin.site.register(MailingCron, MailingCronAdmin)
admin.site.register(Mailing, MailingAdmin)
admin.site.register(Subscriber, SubscriberAdmin)
admin.site.register(SMSTask, SMSTaskAdmin)
admin.site.register(SMSText, SMSTextAdmin)
