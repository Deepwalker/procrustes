# (c) Svarga project under terms of the new BSD license

from functools import partial

from procrustes import validators

__version__ = '0.1'


class Procrustes(object):
    def __init__(self):
        self.validators = {}

    def __getattr__(self, validator):
        if validator in self.validators:
            return partial(create_class, validator)
        raise AttributeError(validator)

    def register(self, name, cls):
        self.validators[name] = cls

    Declarative = validators.Declarative


def create_class(validator, *args, **kwargs):
    cls = procrustes.validators[validator]
    new_cls = type('Pc' + validator, (cls, ), {})
    new_cls.required = kwargs.pop('required', True)
    new_cls.configure(*args, **kwargs)
    return new_cls


procrustes = Procrustes()
ValidationError = validators.ValidationError


for name, validator in {
    'Tuple': validators.Tuple,
    'List': validators.List,
    'Dict': validators.Dict,
    'String': validators.String,
    'Integer': validators.Integer,
    }.iteritems():
    procrustes.register(name, validator)
