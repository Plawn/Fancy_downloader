import json
from Fancy_downloader import Download, from_save

with open('test.zip.json', 'r') as f :
    data = json.loads(f.read())

d = from_save(data)
d.download()