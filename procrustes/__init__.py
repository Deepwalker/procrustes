# (c) Svarga project under terms of the new BSD license

__version__ = '0.1'

from functools import partial
from procrustes.register import procrustes
from procrustes import validators
from procrustes.pforms import forms


ValidationError = validators.ValidationError

procrustes.Declarative = validators.Declarative
