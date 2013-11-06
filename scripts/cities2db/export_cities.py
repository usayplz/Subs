#!/usr/bin/python
# -*- coding: utf-8 -*-

import re, codecs

filename = 'list_cities.csv'
f = codecs.open(filename, "r", 'utf-8')
for line in f:
    line = line.strip()
    m = re.match(ur'(\w+),(("[А-Яа-я ,-\.]+\s([А-Яа-я-ё]+)")|("[А-Яа-я ,-\.]+\.([А-Яа-я-ё]+)")|([А-Яа-я-ё]+)),', line, re.U)
    if m:
        if m.groups()[3] is None:
            point = m.groups()[1].encode('utf-8')
        else:
            point = m.groups()[3].encode('utf-8')
        print m.groups()[0].encode('utf-8'), point
