from setuptools import setup

with open('readme.md', 'r') as f :
    readme_content = f.read()

setup(
    name='petit_downloader',
    version='0.1.7',
    description='Download files in an easier way',
    packages=['petit_downloader'],
    url='https://github.com/Plawn/petit_downloader',
    license='apache-2.0',
    author='Plawn',
    author_email='plawn.yay@gmail.com',
    long_description=readme_content,
    long_description_content_type="text/markdown",
)
