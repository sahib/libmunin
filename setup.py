from setuptools import setup
from pip.req import parse_requirements
from munin import __version__, __url__


print("""Please make sure to have these third party tools installed:

    - moodbar: http://pwsp.net/~qbob/moodbar-0.1.2.tar.gz
    - bpm-utils: ttp://www.pogo.org.uk/~mark/bpm-tools/
""")

# parse_requirements() returns generator of pip.req.InstallRequirement objects
try:
    install_reqs = list(parse_requirements('pip_requirements.txt'))
except:
    install_reqs = list(parse_requirements('https://raw.github.com/sahib/libmunin/master/pip_requirements.txt'))


setup(
    name='libmunin',
    version=__version__,
    description='Fancy library for music recommendations, based on datamining algorithms',
    long_description=open('README.rst').read(),
    url=__url__,
    author='Christopher Pahl',
    author_email='sahib@online.de',
    license='GPLv3',
    packages=['munin'],
    install_requires=[str(ir.req) for ir in install_reqs]
)
