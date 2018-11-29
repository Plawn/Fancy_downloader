import requests

class Action:
    """
    A function to execute, followed by its args
    """

    def __init__(self, func, *args):
        self.function = func
        self.args = [*args]

    def __call__(self): self.function(*self.args)

End_action = Action
Begin_action = Action


def url_size(url):
    r = requests.head(url, headers={'Accept-Encoding': 'identity'})
    return(int(r.headers.get('content-length', 0)), r)


def sm_split(sizeInBytes, numsplits, offset = 0):
    if numsplits <= 1:
        return ["0-{}".format(sizeInBytes)]
    lst = []
    i = 0
    lst.append('%s-%s' % (i + offset, offset + int(round(1 + i * sizeInBytes/(numsplits*1.0) + sizeInBytes/(numsplits*1.0)-1, 0))))
    for i in range(1, numsplits):
        lst.append('%s-%s' % (offset + int(round(1 + i * sizeInBytes/(numsplits*1.0),1)), offset + int(round(1 + i * sizeInBytes/(numsplits*1.0) + sizeInBytes/(numsplits*1.0)-1, 0))))
    return lst

def extract_nb(string):
    s = ""
    for i in string:
        if i in "0123456789":
            s += i
    return(s)