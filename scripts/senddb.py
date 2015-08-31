#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mail import send_mail
import os, time

os.system("rm -f /tmp/subs*")
os.system("mysqldump -uroot -pkanefron7 sw > /tmp/subsdb.sql")
time.sleep(5)
#os.system("bzip2 /tmp/subsdb.sql")
#time.sleep(30)
os.system("scp -P 443 /tmp/subsdb.sql  root@95.85.31.41:/var/www/temp/")
#send_mail('subs@foxthrottle.com', ['usayplz@gmail.com'], 'subs', 'database backup', ['/tmp/subsdb.sql.bz2'])