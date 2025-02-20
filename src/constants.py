from os.path import dirname, abspath, join

__all__ = ['SOURCE']

# makes dealing with filepaths handy
class PATH:
    parent:'PATH'
    value:str

    def __init__(self,value:str,parent=None,**kwargs):
        if parent is not None:
            if not isinstance(parent, PATH):
                raise TypeError("Parent must be of type PATH")
        if not isinstance(value, str):
            raise TypeError("Value must be a string")
        self.parent = parent
        self.value = value
        for k, v in kwargs.items():
            if not isinstance(v, PATH) and k not in ['parent', 'value']:
                raise TypeError("Value must be of type PATH")
            setattr(self, k, v)
            setattr(v, "parent", self)

    def __getitem__(self, key):
        return getattr(self, key)

    def __repr__(self):
        return str({K:V for K,V in self.__dict__.items() if K != 'parent'})
    
    @property
    def str(self)->str:
        if self.parent is None:
            return self.value
        return join(self.parent.str, self.value)
    @property
    def leaves(self):
        ls = list()
        for k,v in self.__dict__.items():
            if k not in ['parent', 'value']:
                ls.append(v)
        if len(ls) == 0:
            return [self.str]
        return [leaf for branch in ls for leaf in branch.leaves]
    
    def format(self,**kwargs)->str:
        return self.str.format(**kwargs)




DB = PATH(value = 'database.db')
DATA = PATH(value = 'data',DB = DB)

LOGS = PATH(value = 'apiLogs.log')
ASSETS = PATH(value = 'assets',LOGS = LOGS)

SOURCE = PATH(value = abspath(join(dirname(__file__),'..')),DATA = DATA,ASSETS = ASSETS)


