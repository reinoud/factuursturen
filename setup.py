#!/usr/bin/env python

from distutils.core import setup
from setuptools.command.test import test as TestCommand
import sys

PROJECT = 'factuursturen'
VERSION = '0.4'
URL = 'https://github.com/reinoud/factuursturen'
AUTHOR = 'Reinoud van Leeuwen'
AUTHOR_EMAIL = 'reinoud.v@n.leeuwen.net'
DESC = "a REST client class for the API of www.factuursturen.nl"



class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ['factuursturen']
        self.test_suite = True
    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)

setup(
    name=PROJECT,
    version=VERSION,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    packages=['factuursturen'],
    url=URL,
    tests_require=['pytest'],
    cmdclass = {'test': PyTest},
    license=open('LICENSE').read(),
    description=DESC,
    long_description=open('README.txt').read(),
    install_requires = ['requests'],
)