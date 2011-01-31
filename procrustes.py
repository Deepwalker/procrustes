# (c) Svarga project under terms of the new BSD license

from functools import partial
from collections import defaultdict


class Procrustes(object):
    def __init__(self):
        self.validators = {}

    def __getattr__(self, validator):
        if validator in self.validators:
            return partial(create_class, validator)
        raise AttributeError(validator)

    def register(self, name, cls):
        self.validators[name] = cls

procrustes = Procrustes()


class PBase(object):
    def __init__(self, data, validate=True):
        self.raw_data = data
        self.validated_data = None
        self.error = None
        if validate:
            self.safe_validate()

    @staticmethod
    def configure(cls, *args, **kwargs):
        raise NotImplementedError('Define `configure` method')

    def validate(self):
        '''Validate data and return it
        '''
        if not self.required and self.raw_data is None:
            return None
        return self.real_validate()

    def real_validate(self):
        '''Inner validate function, without `required` flag check
        '''
        raise NotImplementedError('Define `real_validate` method')

    def safe_validate(self):
        try:
            self.validated_data = self.validate()
        except ValidationError as e:
            self.error = e.args[0]

    @property
    def data(self):
        return self.validated_data

    def flatten(self, delimiter='__'):
        '''Make a version of value suitable to use in flat dictionary
        '''
        yield '', self.validated_data

    @classmethod
    def bulge(cls, flat):
        '''Return a canonical version of a flat representation of value
        '''
        if flat is None:
            return None
        try:
            return flat['']
        except (KeyError, TypeError):
            return None


class PTuple(PBase):
    @staticmethod
    def configure(cls, *types):
        cls.types = types

    def real_validate(self):
        data = tuple(self.raw_data)
        if len(self.types) != len(data):
            raise ValidationError('Must be iterable of length %i'
                                  % len(self.types))
        instances = [t(value, True) for t, value in zip(self.types, data)]
        errors = [i.error for i in instances if i.error]
        if errors:
            raise ValidationError(errors)
        return instances

    @property
    def data(self):
        if not self.validated_data:
            return
        return tuple(i.data for i in self.validated_data)

    def flatten(self, delimiter='__'):
        for number, value in enumerate(self.validated_data):
            for key, data in value.flatten(delimiter):
                tail = delimiter + key if key else ''
                yield str(number) + tail, data

    @classmethod
    def bulge(cls, flat, delimiter='__'):
        i = 0
        collector = []
        for key, flatchild in sorted(group_by_key(flat, delimiter).iteritems()):
            try:
                number = int(key)
            except ValueError:
                continue
            if i < number:
                # TODO OMG
                collector.extend([None] * (number - i))
                i = number - 1
            collector.append(cls.types[number].bulge(flatchild))
            i = i + 1
        return tuple(collector)


class PList(PBase):
    @staticmethod
    def configure(cls, type):
        cls.type = type

    def real_validate(self):
        instances = [self.type(i, True) for i in list(self.raw_data)]
        errors = [i.error for i in instances if i.error]
        if errors:
            raise ValidationError(errors)
        return instances

    @property
    def data(self):
        if not self.validated_data:
            return
        return [i.data for i in self.validated_data]

    def flatten(self, delimiter='__'):
        for number, value in enumerate(self.validated_data):
            for key, data in value.flatten(delimiter):
                tail = delimiter + key if key else ''
                yield str(number) + tail, data

    @classmethod
    def bulge(cls, flat, delimiter='__'):
        return [cls.type.bulge(flatchild) for flatchild in
                group_by_key(flat, delimiter).itervalues()]


class PDict(PBase):
    @staticmethod
    def configure(cls, named_types):
        cls.named_types = named_types

    def real_validate(self):
        instances = {}
        for name, typ in self.named_types.iteritems():
            instances[name] = typ(self.raw_data.get(name, None), True)
        errors = dict((name, value.error) for name, value
                      in instances.iteritems() if value.error)
        if errors:
            raise ValidationError(errors)
        return instances

    @property
    def data(self):
        if not self.validated_data:
            return
        return dict((name, value.data) for name, value
                    in self.validated_data.iteritems())

    def flatten(self, delimiter='__'):
        for name, value in self.validated_data.items():
            for key, data in value.flatten(delimiter):
                tail = delimiter + key if key else ''
                yield name + tail, data

    @classmethod
    def bulge(cls, flat, delimiter='__'):
        result = {}
        grouped = group_by_key(flat, delimiter)
        for name, ftype in cls.named_types.items():
            flatchild = grouped.pop(name, None)
            result[name] = ftype.bulge(flatchild)
        # TODO we may have unmatched data in `grouped`
        return result


class PString(PBase):
    @staticmethod
    def configure(cls, min_length=None, max_length=None, regex=None):
        cls.min_length = min_length
        cls.max_length = max_length
        cls.regex = regex

    def real_validate(self):
        s = str(self.raw_data)
        slen = len(s)

        if self.min_length is not None and slen < self.min_length:
            raise ValidationError('Must be longer then %i' % self.min_length)
        if self.max_length is not None and slen > self.max_length:
            raise ValidationError('Must be shorter then %i' % self.max_length)

        return s


class PInteger(PBase):
    @staticmethod
    def configure(cls, min=None, max=None):
        cls.min = min
        cls.max = max

    def real_validate(self):
        try:
            i = int(self.raw_data)
        except (ValueError, TypeError):
            raise ValidationError('Must be number, not a string')

        if self.min is not None and i < self.min:
            raise ValidationError('Must be larger then %i' % self.min)
        if self.max is not None and i > self.max:
            raise ValidationError('Must be smaller then %i' % self.max)

        return i


for name, validator in {
    'Tuple': PTuple,
    'List': PList,
    'Dict': PDict,
    'String': PString,
    'Integer': PInteger,
    }.iteritems():
    procrustes.register(name, validator)


# Helpers
def create_class(validator, *args, **kwargs):
    cls = procrustes.validators[validator]
    new_cls = type('Pc' + validator, (cls, ), {})
    new_cls.required = kwargs.pop('required', True)
    cls.configure(new_cls, *args, **kwargs)
    return new_cls


def group_by_key(flat, delimiter='__'):
    def split_key(flat):
        for key, value in sorted(flat.iteritems()):
            keys = key.split(delimiter, 1)
            base_key = keys[0]
            child_key = keys[1] if len(keys) == 2 else ''
            yield base_key, child_key, value

    collector = defaultdict(dict)
    for key, child_key, value in split_key(flat):
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
    flat = dict(pt.flatten())
    print 'Flatten:', flat
    print 'Unflatten:', PT.bulge(flat)

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
    flat = dict(pt.flatten())
    print 'Flatten:', flat
    flat = {'2__b': 'sdfsdf', '2__c__0': 0, '2__c__1': 1, '2__c__2': 2,
               '1': '234234', '0': 9}
    print 'Unflatten:', PT.bulge(flat)

    pt = PT(PT.bulge(flat))
    print 'All:', pt.data, pt.error
