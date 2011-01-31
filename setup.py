#!/usr/bin/env python

import os.path as op
act = op.join(op.dirname(__file__), 'venv', 'bin', 'activate_this.py')
if op.exists(act):
    execfile(act, {'__file__': act})

import os.path
from setuptools import setup, find_packages

import procrustes


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setupconf = dict(
    name = 'procrustes',
    version = procrustes.__version__,
    license = 'BSD',
    url = 'https://github.com/Deepwalker/Procrustes/',
    author = 'Svarga Developers',
    author_email = 'svarga@librelist.com',
    description = ('validation library'),
    long_description = read('README.rst'),

    packages = find_packages(),

    classifiers = [
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        ],
    )

if __name__ == '__main__':
    setup(**setupconf)
