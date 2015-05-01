#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-

import os

def check_pid(pid):        
    """ Check For the existence of a unix pid. """
    if pid:
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        else:
            return True
    else:
        return False


def write_pid(path):
    try:
        fh = open(os.path.join(os.path.dirname(__file__), path), "w")
        try:
            fh.write(str(os.getpid()))
        finally:
            fh.close()
    except IOError, e:
        raise


def read_pid(path):
    pid = 0
    try:
        fh = open(os.path.join(os.path.dirname(__file__), path), "r")
        try:
            pid = fh.read()
        finally:
            fh.close()
            return pid
    except IOError, e:
        return pid
