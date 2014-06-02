#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mail import send_mail
import os, time

os.system("rm -f /tmp/subs*")
os.system("mysqldump -uroot -pkanefron7 subsdb > /tmp/subsdb.sql")
time.sleep(30)
os.system("bzip2 /tmp/subsdb.sql")
time.sleep(30)
send_mail('subs@foxthrottle.com', ['metasize@gmail.com'], 'subs', 'database backup', ['/tmp/subsdb.sql.bz2'])