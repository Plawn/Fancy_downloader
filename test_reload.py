import json
import hashlib

import Fancy_progressbar as fp

from petit_downloader import from_save


def md5(fname: str):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


with open('test.zip.json', 'r') as f:
    data = json.loads(f.read())
md5_for_url = "301c7b5f09b373ffc55e38f75c2e4027"

b = fp.ProgressBar('download', 'kill_when_finished', 'animated')
d = from_save(data)
handle = fp.ProgressBarHandler([b])
handle.start()
b.use_progress(d.get_progression)
d.download()
b.finish()

assert md5_for_url == md5('test.zip')