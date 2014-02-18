import datetime

__author__ = 'tmehta'


def divide_timedelta(td, divisor):
    divided_seconds = td.total_seconds() / float(divisor)
    return datetime.timedelta(seconds=divided_seconds)