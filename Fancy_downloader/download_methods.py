import threading
import time

import requests

from . import Fancy_downloader as dl
from . import aux_func as aux
from . import constants


def get_and_retry(url, split='', d_obj=None, session=None):
    header, done, errors = {}, False, 0
    while not done:
        header['Range'] = 'bytes={}'.format(split)
        response = None 
        if session == None:
            response = requests.get(url, headers=header, stream=True)
        else :
            response = session.get(url, headers=header, stream=True)
        if response.status_code in constants.SUCCESS_CODES:
            done = True
            return response
        else:
            errors += 1
            print("error retrying | error code {}".format(response.status_code))
            time.sleep(constants.RETRY_SLEEP_TIME)
            if errors == constants.MAX_RETRY:
                print('Download canceled')
                d_obj.has_error = True
                d_obj.stop()
                raise Exception("Error max retry")


def get_chunk(url, split, d_obj, session=None):
    l = split.split('-')
    response = get_and_retry(url, split, d_obj, session)
    at = int(l[0])
    for data in response.iter_content(chunk_size=d_obj.chunk_size):
        if not d_obj.is_stopped():
            at = d_obj.write_at(at, data)
            if d_obj.is_paused():
                d_obj.event.wait(d_obj.pause_time)
        else:
            return False
    return True


def serial_chunked_download(d_obj, end_action=None, session=None, start=0, end=0):
    """Downloads a file using a single connection getting a chunk at a time
    """
    splits = None
    if start == 0 and end == 0:
        d_obj.init_size()
        d_obj.init_file()
        nb_split = 0
        if d_obj.split_size != -1:
            nb_split = int(d_obj.size / d_obj.split_size) + 1
        else:
            nb_split = d_obj.nb_split
        splits = aux.sm_split(d_obj.size, nb_split)
    else:
        nb_split = int(d_obj.size / d_obj.split_size) + 1
        splits = aux.sm_split(end - start, nb_split, start)
    
    for split in splits:
        get_chunk(d_obj.url, split, d_obj, session)
        if d_obj.has_error or d_obj.is_stopped():
            print('has error')
            return False

    if end_action != None:
        end_action()
    if end == 0 and start == 0:
        d_obj.finish()
        print('{}-{} is finished'.format(start, end))
    return True


def parralel_chunked_download(d_obj, end_action=None):
    """Downloads a file using multiple connections
    """
    d_obj.init_size()
    splits = aux.sm_split(d_obj.size, d_obj.nb_split)
    threads = []
    d_obj.init_file()
    for split in splits:
        t = threading.Thread(target=get_chunk, args=(d_obj.url, split, d_obj))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

    if d_obj.has_error:
        return False
    if end_action != None:
        end_action()
    d_obj.finish()
    return True


def basic_download(d_obj, end_action=None, session=None):
    """Downloads a file using a single connection in a single chunk
    """
    d_obj.init_size()
    d_obj.init_file()

    get_chunk(d_obj.url, "{}-{}".format(0, d_obj.size), d_obj, session)
    if end_action != None:
        end_action()
    d_obj.finish()
    return True


def serial_parralel_chunked_download(d_obj, end_action=None, session=None):
    """Downloads a file using multiple connections and multiple chunks per connection
    """
    d_obj.init_size()
    size = d_obj.size
    splits = aux.sm_split(size, d_obj.nb_split)
    threads = []
    d_obj.init_file()
    end_action1 = None
    for split in splits:
        l = split.split('-')

        start, end = int(l[0]), int(l[1])
        t = threading.Thread(target=serial_chunked_download,
                             args=(d_obj, end_action1, session,start, end))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    if d_obj.has_error:
        return False
    if end_action != None:
        end_action()
    d_obj.finish()
    return False


METHODS = {
    "serial_chunked": serial_chunked_download,
    "parralel_chunked": parralel_chunked_download,
    "basic": basic_download,
    "serial_parralel_chunked": serial_parralel_chunked_download
}
