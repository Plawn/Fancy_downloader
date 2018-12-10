[Latest Version = 0.15]

##[Installation]

```shell
	pip install Fancy_Downloader
```

##[How to use]

```python
	import Fancy_Downloader as dl
	d = dl.Download(url=url, type="serial_chunked") #verbose requeries the Fancy_Progressbar lib
	dl.download(d)
	
```
#[Download types available]

* serial_chunked
* basic
* parrarel_chunked
* serial_parralel_chunked

# Objects available

```python
	Download()
	Download_container()
	Action(func, *args)

```
#[Functions available]
```python
	download(Download_objet) #deprecated

```

