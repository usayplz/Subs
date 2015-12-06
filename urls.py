# -*- coding: utf-8 -*-

from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'sw.views.index'),
    url(r'^wsdl$', 'sw.views.wsdl'),
    url(r'^admin_tools/', include('admin_tools.urls')),
    url(r'^admin/', include(admin.site.urls)),
    ('^pages/', include('django.contrib.flatpages.urls')),

    #url(r'^rtsoapservice/', 'rtsoapservice.views.rt_soap_service'),
)
