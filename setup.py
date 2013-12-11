from setuptools import setup
from pip.req import parse_requirements


print("""Please make sure to have these third party tools installed:

    - moodbar: http://pwsp.net/~qbob/moodbar-0.1.2.tar.gz
    - bpm-utils: ttp://www.pogo.org.uk/~mark/bpm-tools/
""")

# parse_requirements() returns generator of pip.req.InstallRequirement objects
install_reqs = parse_requirements('pip_requirements.txt')


setup(
    name='libmunin',
    version='0.1.1-git',
    description='Fancy library for music recommendations, based on datamining algorithms',
    long_description=open('README.rst').read(),
    url='http://libmunin-api.readthedocs.org/en/latest/index.html',
    author='Christopher Pahl',
    author_email='sahib@online.de',
    license='GPLv3',
    packages=['munin'],
    install_requires=[str(ir.req) for ir in install_reqs]
)
