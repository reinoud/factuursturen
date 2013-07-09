#!/usr/bin/env python

from distutils.core import setup
#from setuptools import setup

PROJECT = 'factuursturen'
VERSION = '0.2'
URL = 'https://github.com/reinoud/factuursturen'
AUTHOR = 'Reinoud van Leeuwen'
AUTHOR_EMAIL = 'reinoud.v@n.leeuwen.net'
DESC = "a REST client class for the API of www.factuursturen.nl"

setup(
    name=PROJECT,
    version=VERSION,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    packages=['factuursturen', 'factuursturen.test'],
    url=URL,
    test_suite = "facuursturen.test.test_client",
    license=open('LICENSE').read(),
    description=DESC,
    long_description=open('README.txt').read(),
)
