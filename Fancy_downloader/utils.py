import requests
from typing import Tuple, List, Dict


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


def get_size(url: str, session: requests.Session = None) -> Tuple[int, requests.Request]:
    requester = session if session is not None else requests
    r = requester.head(url, headers={'Accept-Encoding': 'identity'})
    return (int(r.headers.get('content-length', 0)), r)


def sm_split(sizeInBytes: int, numsplits: int, offset: int = 0) -> List[str]:
    if numsplits <= 1:
        return [f"0-{sizeInBytes}"]
    lst = []
    i = 0
    lst.append('%s-%s' % (i + offset, offset + int(round(1 + i *
                                                         sizeInBytes/(numsplits*1.0) + sizeInBytes/(numsplits*1.0)-1, 0))))
    for i in range(1, numsplits):
        lst.append('%s-%s' % (offset + int(round(1 + i * sizeInBytes/(numsplits*1.0), 1)), offset +
                              int(round(1 + i * sizeInBytes/(numsplits*1.0) + sizeInBytes/(numsplits*1.0)-1, 0))))
    return lst


def extract_int(string: str) -> str:
    return ''.join(i for i in string if i in '0123456789')



def prepare_name(url:str) -> str :
    splited = url.split('/')
    resized = ''
    try:
        resized = splited[-1][:20] + '.' + splited[-1].split('.')[1]
    except:
        resized = splited[-1][:30]
    return resized