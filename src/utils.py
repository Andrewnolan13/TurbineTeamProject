from typing import get_type_hints
import os
import datetime as dt
import argparse

def enforce_types(func):
    def wrapper(*args, **kwargs):
        hints = get_type_hints(func)
        # Enforce argument types
        for name, value in zip(func.__code__.co_varnames, args):
            if name in hints and not isinstance(value, hints[name]):
                raise TypeError(f"Argument {name} must be {hints[name]}, got {type(value).__name__}")

        # Call the function
        result = func(*args, **kwargs)

        # Enforce return type
        if "return" in hints and not isinstance(result, hints["return"]):
            raise TypeError(f"Return value must be {hints['return']}, got {type(result).__name__}")

        return result

    return wrapper

def kill_python_processes():
    # image_name = get_python_image_name()
    # cmd = "taskkill /im {} /f".format(image_name)
    cmd = "taskkill /f /pid {}".format(os.getpid())
    os.system(cmd)

def secondsTillEndOf(t:str):
    if t == 'minutely':
        return 60 - dt.datetime.now().second
    if t == 'hourly':
        return 3600 - dt.datetime.now().minute*60 - dt.datetime.now().second
    if t == 'daily':
        return 86400 - dt.datetime.now().hour*3600 - dt.datetime.now().minute*60 - dt.datetime.now().second
    else:
        raise ValueError('Invalid time unit. Must be minutely, hourly or daily')
    
def parseArgs():
    parser = argparse.ArgumentParser(description='Real-time Wind Turbine Forecasting Dashboard')
    parser.add_argument('--predictionWindow', type = float, default = 7.0,help='The time window in days for which to make predictions. Can be a decimal.')
    return parser.parse_args()