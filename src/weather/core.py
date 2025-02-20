from .abstract_classes import AbstractForecastAPI, AbstractHistoricalAPI

'''
Here I will write logic to read/write from db. Special logic for requests etc.
'''
class ForecastAPI(AbstractForecastAPI):
    def __init__(self):
        super().__init__()
    def request(self):
        # special logic here
        return super()._request()
    

class HistoricalAPI(AbstractHistoricalAPI):
    def __init__(self):
        super().__init__()
    def request(self):
        # special logic here
        return super()._request()
        