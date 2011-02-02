# (c) Svarga project under terms of the new BSD license

from functools import partial, wraps


class Procrustes(object):
    def __init__(self):
        self.validators = {}

    def __getattr__(self, validator):
        if validator in self.validators:
            return partial(create_class, validator)
        raise AttributeError(validator)

    def register(self, *args):
        largs = len(args)
        def wrapper(validator):
            validator_name = args[0] if largs else validator.__name__
            self.register(validator_name, validator)
            return validator

        if largs==2:
            self.validators[args[0]] = args[1]
        else:
            return wrapper

procrustes = Procrustes()


def create_class(validator, *args, **kwargs):
    cls = procrustes.validators[validator]
    new_cls = type('Pc' + validator, (cls, ), {})
    new_cls.required = kwargs.pop('required', True)
    new_cls.configure(*args, **kwargs)
    return new_cls
