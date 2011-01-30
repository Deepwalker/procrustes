# Procrustes
from functools import partial
from sorteddict import sorteddict
from collections import defaultdict


class Procrustes(object):
    def __getattr__(self, validator):
        if validator in register:
            return partial(create_class, validator)
        raise AttributeError, validator

procrustes = Procrustes()


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
        if not self.required and self._data is None:
            return None
        return self.real_validate()

    def real_validate(self):
        raise NotImplementedError, 'Define `validate` method'

    def safe_validate(self):
        try:
            self.validated_data = self.validate()
        except ValidationError as e:
            self.error = e.args[0]

    @property
    def data(self):
        return self.validated_data

    def flatten(self, delimiter='__'):
        yield '', self.validated_data

    @classmethod
    def from_flatten(cls, flatten):
        if flatten is None:
            return None
        try:
            return flatten['']
        except KeyError, TypeError:
            return None


class PTuple(PBase):
    @staticmethod
    def configure(cls, *types):
        cls._types = types

    def real_validate(self):
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

    def flatten(self, delimiter='__'):
        for number, value in enumerate(self.validated_data):
            for key, data in value.flatten(delimiter):
                tail = delimiter + key if key else ''
                yield str(number) + tail, data

    @classmethod
    def from_flatten(cls, flatten, delimiter='__'):
        i = 0
        collector = []
        for key, child_flatten in sorted(group_by_key(flatten, delimiter).items()):
            try:
                number = int(key)
            except ValueError:
                continue
            if i < number:
                # TODO OMG
                collector.extend([None] * (number - i))
                i = number - 1
            collector.append(cls._types[number].from_flatten(child_flatten))
            i = i + 1
        return collector


class PList(PBase):
    @staticmethod
    def configure(cls, _type):
        cls._type = _type

    def real_validate(self):
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

    def flatten(self, delimiter='__'):
        for number, value in enumerate(self.validated_data):
            for key, data in value.flatten(delimiter):
                tail = delimiter + key if key else ''
                yield str(number) + tail, data

    @classmethod
    def from_flatten(cls, flatten, delimiter='__'):
        return [cls._type.from_flatten(child_flatten) for child_flatten in 
                                      group_by_key(flatten, delimiter).values()]


class PDict(PBase):
    @staticmethod
    def configure(cls, named_types):
        cls._named_types = named_types

    def real_validate(self):
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

    def flatten(self, delimiter='__'):
        for name, value in self.validated_data.items():
            for key, data in value.flatten(delimiter):
                tail = delimiter + key if key else ''
                yield name + tail, data

    @classmethod
    def from_flatten(cls, flatten, delimiter='__'):
        result = {}
        grouped = group_by_key(flatten, delimiter)
        for name, ftype in cls._named_types.items():
            child_flatten = grouped.pop(name, None)
            result[name] = ftype.from_flatten(child_flatten)
        #TODO we may have in `grouped` unmatched data
        return result


class PString(PBase):
    @staticmethod
    def configure(cls, min_length=None, max_length=None, regex=None):
        cls.min_length = min_length
        cls.max_length = max_length
        cls.regex = regex

    def real_validate(self):
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

    def real_validate(self):
        try:
            i = int(self._data)
        except (ValueError, TypeError) as e:
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


# Helpers
def create_class(validator, *args, **kwargs):
    cls = register[validator]
    new_cls = type('Pc' + validator, (cls, ), {})
    new_cls.required = kwargs.pop('required', True)
    cls.configure(new_cls, *args, **kwargs)
    return new_cls


def group_by_key(flatten, delimiter='__'):
    def split_key(flatten):
        for key, value in sorted(flatten.items()):
            keys = key.split(delimiter, 1)
            base_key = keys[0]
            child_key = keys[1] if len(keys)==2 else ''
            yield base_key, child_key, value

    collector = defaultdict(lambda: {})
    for key, child_key, value in split_key(flatten):
        collector[key][child_key] = value
    return collector


# Exceptions
class ValidationError(Exception):
    pass


if __name__ == '__main__':
    I = procrustes.Integer(max=90, required=False)
    S = procrustes.String()
    I(10).validate()
    I(100).safe_validate()
    S('kuku').validate()
    S('keke').safe_validate()

    PL = procrustes.List(I)
    PT = procrustes.Tuple(I, S, I)
    pt = PT([10, 'sdfsdf', 30])
    print 'Tuple:', pt.data, pt.error
    flatten = dict(pt.flatten())
    print 'Flatten:', flatten
    print 'Unflatten:', PT.from_flatten(flatten)

    pl = PL(xrange(10))
    print 'List:', pl.data, pl.error

    PT = procrustes.Tuple(I, S, PL)
    pt = PT((9, '234234', xrange(3)))
    print 'Tuple and List:', pt.data, pt.error
    print dict(pt.flatten())

    PD = procrustes.Dict({'a': I, 'b': S, 'c': PL})
    pd = PD({'a': 34, 'b': 'sdfsdf', 'c': xrange(3)})
    print 'Dict and List:', pd.data, pd.error
    print dict(pd.flatten())

    PT = procrustes.Tuple(I, S, PD)
    pt = PT((9, '234234', {'a': 34, 'b': 'sdfsdf', 'c': xrange(3)} ))
    print 'All:', pt.data, pt.error
    flatten = dict(pt.flatten())
    print 'Flatten:', flatten
    flatten = {'2__b': 'sdfsdf', '2__c__0': 0, '2__c__1': 1, '2__c__2': 2, '1': '234234', '0': 9}
    print 'Unflatten:', PT.from_flatten(flatten)

    pt = PT(PT.from_flatten(flatten))
    print 'All:', pt.data, pt.error
