python3 setup.py bdist_wheel 
twine upload dist/*
rm -Rf dist build Fancy_progressbar.egg-info