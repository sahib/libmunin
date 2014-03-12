from setuptools import setup
from munin import __version__, __url__



print("""Please make sure to have these third party tools installed:

    - moodbar: http://pwsp.net/~qbob/moodbar-0.1.2.tar.gz
    - bpm-utils: ttp://www.pogo.org.uk/~mark/bpm-tools/
""")

# Sadly, this does not work on Debian (wat. Debian, get your stuff together.)
# So, we just fake it.
# from pip.req import parse_requirements
import urllib.request


def parse_requirements(url):
    text = None
    protocol, path = url.split('://', 1)
    if protocol == 'file':
        try:
            with open(path, 'r') as handle:
                text = handle.read()
        except:
            pass
    else:
        text = urllib.request.urlopen(url).read()

    for line in text.splitlines():
        line = line.strip()
        if not line.startswith('#') and line:
            yield line


try:
    install_reqs = list(parse_requirements('file://pip_requirements.txt'))
except:
    install_reqs = list(parse_requirements(
        'https://raw.github.com/sahib/libmunin/master/pip_requirements.txt'
    ))

print('IR', install_reqs)

setup(
    name='libmunin',
    version=__version__,
    description='Fancy library for music recommendations, based on datamining algorithms',
    long_description=open('README.rst').read(),
    url=__url__,
    author='Christopher Pahl',
    author_email='sahib@online.de',
    license='GPLv3',
    packages=[
        'munin',
        'munin.distance',
        'munin.provider',
        'munin.scripts',
        'munin.stopwords',
    ],
    package_data={
        'munin.stopwords': ['data/*'],
        'munin.provider': ['genre.list']
    },
    install_requires=install_reqs
)
