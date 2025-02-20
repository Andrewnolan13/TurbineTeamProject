'''
Custom exceptions.

Why? 

- I will extend every exception from RunTimeException.
- this means I can do:
    try:
        # code
    except RunTimeException as e:
        # handle foreseen exception
        # then check what type of RunTimeException it is
        if isinstance(e, TooManyRequests):
            # handle too many requests
            etc.
    except Exception as e:
        # debug unexpected exception

so every exception I forsee, I will write it here.
'''

class RunTimeException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message
    def __str__(self):
        return self.message

class TooManyRequests(RunTimeException):
    def __init__(self, message = "Too many requests"):
        super().__init__(message)
        self.message = message