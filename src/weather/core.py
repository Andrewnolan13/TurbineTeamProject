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
        # build the url.
        # parse the url into something that can be turned into a SQL query
        # query the data base.
            # if it exists, return it. function terminates here.
        # if it doesn't exist, request the data from the API
        # parse the response to database friendly format
        # write to the database
        # return the data

        return super()._request()
        