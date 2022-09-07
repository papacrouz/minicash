import hashlib

__all__ = [
    "singleton", "Singleton", "mutex"
]



def Hash(s):
	if type(s) == str: s = s.encode()
	if type(s) == dict: s = str(s).encode()
	return hashlib.sha256(s).hexdigest()

	
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