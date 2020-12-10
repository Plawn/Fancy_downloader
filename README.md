[Latest Version = 0.17]

## [Installation]

```sh
$ pip install Fancy_Downloader
```

##[How to use]

```python
	from petit_downloader import Download
	d = Download(url=url, filename="test.zip", type="serial") #verbose requeries the Fancy_Progressbar lib
	d.download()
```
# Download types available

* basic
* serial
* parrarel
* serial_parralel

# Objects available

```python
	Download()
	DownloadContainer()
	Action(func, *args)
```
