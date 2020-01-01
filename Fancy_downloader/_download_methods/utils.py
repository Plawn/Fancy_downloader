import time
import requests

RETRY_SLEEP_TIME = 0.3
MAX_RETRY = 10

def get_and_retry(url, split='', d_obj=None, session: requests.Session = None):
    headers = {
        'Range': f'bytes={split}'
    }
    done = False
    errors = 0
    requester = session if session is not None else requests
    while not done:
        response = requester.get(url, headers=headers, stream=True)
        if response.status_code < 300:
            done = True
            return response
        else:
            errors += 1
            print(f"error retrying | error code {response.status_code}")
            time.sleep(RETRY_SLEEP_TIME)
            if errors == MAX_RETRY:
                print('Download canceled')
                d_obj.has_error = True
                d_obj.stop()
                raise Exception("Error max retry")


def get_chunk(url: str, split, d_obj, session: requests.Session = None):
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