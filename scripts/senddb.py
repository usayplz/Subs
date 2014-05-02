#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mail import send_mail
import os, time

os.system("mysqldump -u root -p kanefron7 --all-databases > /var/www/subs/scripts/cities2db/subsd b.sql")
time.sleep(3)
send_mail('subs@foxthrottle.com', ['metasize@gmail.com'], 'subs', 'database backup', ['/var/www/subs/scripts/cities2db/subsdb.sql'])