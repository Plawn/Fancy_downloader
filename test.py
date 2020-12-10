import hashlib
import sys
import Fancy_progressbar as fp

import Fancy_downloader as dl


def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

url = 'https://download01.logi.com/web/ftp/pub/techsupport/gaming/lghub_installer.zip'
md5_for_url = "301c7b5f09b373ffc55e38f75c2e4027"

# url = 'http://ipv4.download.thinkbroadband.com/1GB.zip'

b = fp.ProgressBar('download', 'kill_when_finished', 'animated')

handle = fp.ProgressBarHandler([b])
handle.start()
d = dl.Download(url, 'test.zip', '', sys.argv[1])
b.use_progress(d.get_progression)
d.download()
b.finish()



assert md5_for_url == md5('test.zip')