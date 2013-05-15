# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from datetime import datetime


# Cron
class MailingCron(models.Model):
    mask = models.CharField(_(u'Маска для задания'), help_text=u'Пример маски: "*-*-* 09:00:00" (ежедневно в 09:00)', default='*-*-* 09:00:00', max_length=255)

    def __unicode__(self):
        return self.mask

    class Meta:
        verbose_name = _(u'Время запуска')
        verbose_name_plural = _(u'Время запуска')


# Рассылки
class Mailing(models.Model):
    name = models.CharField(_(u'Название рассылки'), max_length=255)
    cron = models.ManyToManyField(MailingCron, verbose_name=_(u'Время запуска'), null=True, blank=True)
    create_date = models.DateTimeField(_(u'Дата создания'), auto_now_add=True)
    create_user = models.ForeignKey(User, verbose_name=_(u'Создатель'), null=True, blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _(u'Рассылка')
        verbose_name_plural = _(u'Рассылки')


# Привязка мобильных к рассылкам
class Subscriber(models.Model):
    mobnum = models.CharField(_(u'Мобильный номер'), max_length=12)
    mailing = models.ForeignKey(Mailing, verbose_name=_(u'Рассылка'))

    def __unicode__(self):
        return u"%s - %s" % (self.mobnum, self.mailing)

    class Meta:
        verbose_name = _(u'Подписчик')
        verbose_name_plural = _(u'Подписчики')


# Очередь сообщений
class SMSTask(models.Model):
    SMS_STATUSES = (
        (0, u'не отправлялось'),
        (1, u'отправлено'),
        (2, u'не доставлено'),
        (3, u'доставлено'),
    )

    mobnum = models.CharField(_(u'Мобильный номер'), max_length=12)
    sms_text = models.TextField(_(u'Текст сообщения'))
    delivery_date = models.DateTimeField(_(u'Дата доставки'), default=datetime.now)
    sent_date = models.DateTimeField(_(u'Дата отправки'), null=True, blank=True)
    status = models.SmallIntegerField(_(u'Статус'), choices=SMS_STATUSES, default=0)

    def __unicode__(self):
        return self.mobnum

    class Meta:
        verbose_name = _(u'Очередь сообщений')
        verbose_name_plural = _(u'Очередь сообщений')


# Тексты сообщений
class SMSText(models.Model):
    sms_text = models.TextField(_(u'Текст сообщения'))
    mailing = models.ForeignKey(Mailing, verbose_name=_(u'Рассылка'))
    from_date = models.DateTimeField(_(u'Дата начала периода'), null=True, blank=True)
    to_date = models.DateTimeField(_(u'Дата конца периода'), null=True, blank=True)

    def __unicode__(self):
        return self.sms_text

    class Meta:
        verbose_name = _(u'Текст сообщения')
        verbose_name_plural = _(u'Тексты сообщений')
