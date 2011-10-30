#!/usr/bin/env python

import os.path as op
act = op.join(op.dirname(__file__), 'venv', 'bin', 'activate_this.py')
if op.exists(act):
    execfile(act, {'__file__': act})

import os.path
from setuptools import setup, find_packages



def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setupconf = dict(
    name = 'procrustes',
    version = '0.2.1',
    license = 'BSD',
    url = 'https://github.com/Deepwalker/Procrustes/',
    author = 'Svarga Developers',
    author_email = 'svarga@librelist.com',
    description = ('validation library'),
    long_description = read('README.rst'),

    packages = find_packages(),

    install_requires = ['ordereddict'],
    test_loader = 'attest:Loader',
    test_suite = 'tests.p',

    classifiers = [
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        ],
    )

if __name__ == '__main__':
    setup(**setupconf)
