#!/usr/bin/python

# standar 
import functools
import binascii
import logging 
import hashlib
import struct
import sys




from os.path import (
    expanduser
)
from sys import (
    platform
)


# local
from app import (
    context
)


__all__ = [
    "params_check", "class_params_check", "singleton", "Singleton", "mutex"
]


bchr = chr
if sys.version > '3':
    bchr = lambda x: bytes([x])


hexlify = binascii.hexlify  
unhexlify = binascii.unhexlify



# poor log op
logging.basicConfig(level=logging.INFO, filename="debug.log", format='%(asctime)s %(message)s') # include timestamp



def logg(msg): 
    logging.info(msg)


def GetAppDir():
    # currently suppports linux 
    if not platform == "linux":
        if not platform == "linux2":
            sys.exit(logg("Error: Unsupported platform"))
    return expanduser("~") + "/" + ".stater"


def singleton(cls, *args, **kw):
    instances = {}

    def _singleton():
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]

    return _singleton


class Singleton(object):
    def __new__(cls, *args, **kw):
        if not hasattr(cls, '_instance'):
            orig = super(Singleton, cls)
            cls._instance = orig.__new__(cls, *args, **kw)
        return cls._instance


def class_params_check(*types, **kwtypes):
    """
       check the parameters of a class function, usage: @class_params_check(int, str, (int, str), key1=list, key2=(list, tuple))
    """

    def _decoration(func):
        @functools.wraps(func)
        def _inner(*args, **kwargs):
            result = [isinstance(_param, _type) for _param, _type in zip(args[1:], types)]
            assert all(result), "params_chack: invalid parameters in " + func.__name__
            result = [isinstance(kwargs[_param], kwtypes[_param]) for _param in kwargs if _param in kwtypes]
            # print result
            assert all(result), "params_chack: invalid parameters in " + func.__name__
            return func(*args, **kwargs)

        return _inner

    return _decoration


def params_check(*types, **kwtypes):
    """
    check the parameters of a function, usage: @params_chack(int, str, (int, str), key1=list, key2=(list, tuple))
    """

    def _decoration(func):
        @functools.wraps(func)
        def _inner(*args, **kwargs):
            result = [isinstance(_param, _type) for _param, _type in zip(args, types)]
            assert all(result), "params_chack: invalid parameters in " + func.__name__
            result = [isinstance(kwargs[_param], kwtypes[_param]) for _param in kwargs if _param in kwtypes]
            # print result
            assert all(result), "params_chack: invalid parameters in " + func.__name__
            return func(*args, **kwargs)

        return _inner

    return _decoration