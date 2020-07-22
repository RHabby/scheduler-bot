import functools
from time import sleep


def retry(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(repr(e))
            sleep(1)
            return func(*args, **kwargs)
    return wrapper
