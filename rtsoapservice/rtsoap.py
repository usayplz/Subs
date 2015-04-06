#!/usr/bin/env python
# -*- coding: utf-8 -*-

from soaplib.wsgi import Application
from django.http import HttpResponse


def extract_basic_credentials(request):
    username, password = None, None
    if 'HTTP_AUTHORIZATION' in request.META:
        auth = request.META['HTTP_AUTHORIZATION'].split()
        if len(auth) == 2:
            if auth[0].lower() == "basic":
                username, password = base64.b64decode(auth[1]).split(':')
    return username, password


class Http401(Exception):
    pass


class Http403(Exception):
    pass


class RTSoapApp(Application):
    def authenticate(self, request):
        """Authenticate webservice requesta."""
        ws_username = 'rtamstudio'
        ws_password = 'J(*Dewfhu3)'
        username, password = extract_basic_credentials(request)
        if username == None:
            raise Http401("401 Authentication required.")
        if username != ws_username or password != ws_password:
            raise Http403("403 You're not authorized to use this webservice!")

    csrf_exempt = True
    
    def __call__(self, request):
        # self.authenticate(request)
        django_response = HttpResponse()
        def start_response(status, headers):
            status, reason = status.split(' ', 1)
            django_response.status_code = int(status)
            for header, value in headers:
                django_response[header] = value
        response = super(RTSoapApp, self).__call__(request.META, start_response)
        django_response.content = '\n'.join(response)
        django_response.csrf_exempt = True
        return django_response

