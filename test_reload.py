import json

import Fancy_progressbar as fp

from Fancy_downloader import from_save

with open('test.zip.json', 'r') as f:
    data = json.loads(f.read())


b = fp.ProgressBar('download', 'kill_when_finished', 'animated')
d = from_save(data)
handle = fp.ProgressBarHandler([b])
# handle.start()
b.use_progress(d.get_progression)
d.download()
b.finish()
