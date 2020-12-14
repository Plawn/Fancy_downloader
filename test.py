import hashlib
import sys
import threading
import time

import Fancy_progressbar as fp

import petit_downloader as dl


def md5(fname: str):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


with_fake_user = True

url = 'https://download01.logi.com/web/ftp/pub/techsupport/gaming/lghub_installer.zip'
md5_for_url = "301c7b5f09b373ffc55e38f75c2e4027"

# url = 'http://ipv4.download.thinkbroadband.com/1GB.zip'

b = fp.ProgressBar('download', 'kill_when_finished', 'animated')

handle = fp.ProgressBarHandler([b])
handle.start()
started_at = time.time()
d = dl.Download(url, 'test.zip', '', sys.argv[1])
b.use_progress(d.get_progression)

def fake_user():
    time.sleep(2)
    d.pause()
    time.sleep(5)
    d.resume()

if with_fake_user:
    threading.Thread(target=fake_user).start()

d.download()

if with_fake_user:
    time.sleep(20)


print(f'time elapsed: {time.time() - started_at} s')
b.finish()



assert md5_for_url == md5('test.zip')
