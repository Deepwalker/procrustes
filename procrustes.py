# Procrustes
from functools import partial


class Procrustes(object):
    def __getattr__(self, validator):
        if validator in register:
            return partial(create_class, validator)

procrustes = Procrustes()


def create_class(validator, *args, **kwargs):
    cls = register[validator]
    new_cls = type('Pc' + validator, (cls, ), {})
    cls.configure(new_cls, *args, **kwargs)
    return new_cls


class ValidationError(Exception):
    pass


class PBase(object):
    def __init__(self, data, validate=True):
        self._data = data
        self.validated_data = None
        self.error = None
        if validate:
            self.safe_validate()

    @staticmethod
    def configure(cls, *args, **kwargs):
        raise NotImplementedError, 'Define `configure` method'

    def validate(self):
        raise NotImplementedError, 'Define `validate` method'

    def safe_validate(self):
        try:
            self.validated_data = self.validate()
        except ValidationError as e:
            self.error = e.args[0]

    @property
    def data(self):
        return self.validated_data


class PTuple(PBase):
    @staticmethod
    def configure(cls, *types):
        cls._types = types

    def validate(self):
        data = tuple(self._data)
        if len(self._types) != len(data):
            raise ValidationError, 'Must be %i elements iterable' % len(self._types)
        instances = []
        for t, d in zip(self._types, data):
            instances.append(t(d, True))
        errors = [i.error for i in instances if i.error]
        if errors:
            raise ValidationError, errors
        return instances

    @property
    def data(self):
        if self.validated_data:
            return tuple(i.data for i in self.validated_data)
        else:
            return None


class PList(PBase):
    @staticmethod
    def configure(cls, _type):
        cls._type = _type

    def validate(self):
        instances = [self._type(i, True) for i in list(self._data)]
        errors = [i.error for i in instances if i.error]
        if errors:
            raise ValidationError, errors
        return instances

    @property
    def data(self):
        if self.validated_data:
            return [i.data for i in self.validated_data]
        else:
            return None

class PDict(PBase):
    @staticmethod
    def configure(cls, named_types):
        cls._named_types = named_types

    def validate(self):
        instances = {}
        for name, typ in self._named_types.items():
            instances[name] = typ(self._data.get(name, None), True)
        errors = dict((name, value.error) for name, value in instances.items()
                                                if value.error)
        if errors:
            raise ValidationError, errors
        return instances

    @property
    def data(self):
        if self.validated_data:
            return dict((name, value.data) for name, value in 
                                                    self.validated_data.items())
        else:
            return None


class PString(PBase):
    @staticmethod
    def configure(cls, min_length=None, max_length=None, regex=None):
        cls.min_length = min_length
        cls.max_length = max_length
        cls.regex = regex

    def validate(self):
        s = str(self._data)
        slen = len(s)

        if self.min_length is not None and slen < self.min_length:
            raise ValidationError, 'Must be longer then %i' % self.min_length
        if self.max_length is not None and i > self.max_length:
            raise ValidationError, 'Must be shorter then %i' % self.max_length

        return s


class PInteger(PBase):
    @staticmethod
    def configure(cls, min=None, max=None):
        cls.min = min
        cls.max = max

    def validate(self):
        try:
            i = int(self._data)
        except ValueError as e:
            raise ValidationError, 'Must be number, not string'

        if self.min is not None and i < self.min:
            raise ValidationError, 'Must be larger then %i' % self.min
        if self.max is not None and i > self.max:
            raise ValidationError, 'Must be smaller then %i' % self.max

        return i


register = {
    'Tuple': PTuple,
    'List': PList,
    'Dict': PDict,
    'String': PString,
    'Integer': PInteger,
    }


if __name__ == '__main__':
    I = procrustes.Integer(max=90)
    S = procrustes.String()
    I(10).validate()
    I(100).safe_validate()
    S('kuku').validate()
    S('keke').safe_validate()

    PL = procrustes.List(I)
    PT = procrustes.Tuple(I, S, I)
    pt = PT([10, 'sdfsdf', 30])
    print 'Tuple:', pt.data, pt.error

    pl = PL(xrange(10))
    print 'List:', pl.data, pl.error

    PT = procrustes.Tuple(I, S, PL)
    pt = PT((9, '234234', xrange(3)))
    print 'Tuple and List:', pt.data, pt.error

    PD = procrustes.Dict({'a': I, 'b': S, 'c': PL})
    pd = PD({'a': 34, 'b': 'sdfsdf', 'c': xrange(3)})
    print 'Dict and List:', pd.data, pd.error



