# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _
from datetime import datetime


# Рассылки
class Mailing(models.Model):
    name = models.CharField(_(u'Название рассылки'), db_index=True, max_length=255)
    yrno_location_code = models.CharField(_(u'Идентификатор города yr.no'), max_length=255, null=True, blank=True)
    timezone = models.CharField(_(u'Часовой пояс'), max_length=10, null=True, blank=True, default="+08:00")
    create_date = models.DateTimeField(_(u'Дата создания'), auto_now_add=True)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = _(u'Рассылка')
        verbose_name_plural = _(u'Рассылки')


# Привязка мобильных к рассылкам
class Subscriber(models.Model):
    SUBS_STATUSES = (
        (0, u'подписан'),
        (1, u'не подписан'),
    )

    CONTRACT_STATUSES = (
        (0, u'неизвестно'),
        (1, u'подписан'),
        (2, u'приостановлен'),
        (3, u'заблокирован'),
    )

    mobnum = models.CharField(_(u'Мобильный номер'), db_index=True, max_length=12)
    mailing = models.ForeignKey(Mailing, verbose_name=_(u'Рассылка'))
    status = models.SmallIntegerField(_(u'Статус'), choices=SUBS_STATUSES, default=0)
    create_date = models.DateTimeField(_(u'Дата создания'), auto_now_add=True)
    subs_time = models.TimeField(_(u'Время отправки'), null=True, blank=True)

    request_id = models.IntegerField(_(u'Номер soap запроса'), null=True, blank=True)
    contract_id = models.IntegerField(_(u'Номер контракта в RT'), db_index=True, null=True, blank=True)
    contract_state = models.IntegerField(_(u'Состояние контракта'), choices=CONTRACT_STATUSES, default=0)

    def __unicode__(self):
        return self.mobnum

    class Meta:
        ordering = ['mobnum', 'mailing']
        verbose_name = _(u'Подписчик')
        verbose_name_plural = _(u'Подписчики')


# Очередь сообщений
class SMSTask(models.Model):
    SMS_STATUSES = (
        (-3, u'был заблокирован'),
        (-2, u'не доставлено'),
        (-1, u'не отправлено'),
        (0, u'не отправлялось'),
        (1, u'отправлено'),
        (2, u'доставлено'),
    )

    mobnum = models.CharField(_(u'Мобильный номер'), max_length=12)
    in_text = models.TextField(_(u'Текст входящего сообщения'), null=True, blank=True)
    out_text = models.TextField(_(u'Сообщение для отправки'))
    delivery_date = models.DateTimeField(_(u'Дата доставки'), auto_now_add=True)
    sent_date = models.DateTimeField(_(u'Дата отправки'), null=True, blank=True)
    status = models.SmallIntegerField(_(u'Статус'), choices=SMS_STATUSES, default=0)
    message_id = models.CharField(_(u'Номер сообщения'), db_index=True, max_length=100, null=True, blank=True)
    error = models.TextField(_(u'Текст ошибки'), null=True, blank=True)

    def __unicode__(self):
        return self.mobnum

    class Meta:
        ordering = ['-delivery_date']
        verbose_name = _(u'Очередь сообщений')
        verbose_name_plural = _(u'Очередь сообщений')
        index_together = [
        	['delivery_date', 'status']
        ]


# Лог очереди сообщений
class SMSTaskLog(models.Model):
    SMS_STATUSES = (
        (-3, u'был заблокирован'),
        (-2, u'не доставлено'),
        (-1, u'не отправлено'),
        (0, u'не отправлялось'),
        (1, u'отправлено'),
        (2, u'доставлено'),
    )

    mobnum = models.CharField(_(u'Мобильный номер'), max_length=12)
    in_text = models.TextField(_(u'Текст входящего сообщения'), null=True, blank=True)
    out_text = models.TextField(_(u'Сообщение для отправки'))
    delivery_date = models.DateTimeField(_(u'Дата доставки'), auto_now_add=True)
    sent_date = models.DateTimeField(_(u'Дата отправки'), null=True, blank=True)
    status = models.SmallIntegerField(_(u'Статус'), choices=SMS_STATUSES, default=0)
    message_id = models.CharField(_(u'Номер сообщения'), max_length=100, null=True, blank=True)
    error = models.TextField(_(u'Текст ошибки'), null=True, blank=True)

    def __unicode__(self):
        return self.mobnum

    class Meta:
        ordering = ['-delivery_date']
        verbose_name = _(u'Log очереди сообщений')
        verbose_name_plural = _(u'Log очереди сообщений')


# Тексты
class WeatherText(models.Model):
    mailing = models.ForeignKey(Mailing, db_index=True, verbose_name=_(u'Рассылка'))
    create_date = models.DateTimeField(_(u'Дата создания'), auto_now_add=True)
    text = models.CharField(_(u'Погода'), max_length=1000)
    temperature = models.CharField(_(u'Температура'), max_length=500)
    wcondition = models.CharField(_(u'Условия'), max_length=500)
    wind_direction = models.CharField(_(u'Направление ветра'), max_length=500)
    wind_speed = models.CharField(_(u'Скорость ветра'), max_length=500)
    pressure = models.CharField(_(u'Давление'), max_length=100, null=True, blank=True)
    time_from = models.DateTimeField(_(u'Дата от'), null=True, blank=True)
    time_to = models.DateTimeField(_(u'Дата до'), null=True, blank=True)

    def __unicode__(self):
        return u'%s° C, %s, %s ветер %s м/с' % (self.temperature, self.wcondition, self.wind_direction, self.wind_speed)

    class Meta:
        ordering = ['time_from']
        verbose_name = _(u'Погода')
        verbose_name_plural = _(u'Погода')


# Last payment
class LastPayment(models.Model):
    mobnum = models.CharField(_(u'Мобильный номер'), max_length=12)
    payment_date = models.DateField(_(u'Дата от'), null=True, blank=True)

    def __unicode__(self):
        return u'%s - %s' % (self.mobnum, self.payment_date)

    class Meta:
        ordering = ['payment_date']
        verbose_name = _(u'Последний платеж')
        verbose_name_plural = _(u'Последние платежи')
