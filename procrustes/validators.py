# (c) Svarga project under terms of the new BSD license

import re
from collections import defaultdict, Iterable
from procrustes.register import procrustes
from ordereddict import OrderedDict


class Base(object):
    default_data = None

    def __init__(self, data=None, validate=False):
        self.raw_data = data
        self.validated_data = self.default_data
        self.error = None
        if validate:
            self.validate(safe=True)

    @classmethod
    def configure(cls, *args, **kwargs):
        pass

    def validate(self, safe=False):
        '''Validate data and return it
        '''
        if not self.required and self.raw_data is None:
            return None
        try:
            self.validated_data = self.check_data()
        except ValidationError as e:
            self.error = e.args[0]
            if not safe:
                raise
        return self.validated_data

    def check_data(self):
        '''Inner validate function, without `required` flag check
        '''
        raise NotImplementedError('Define `check_data` method')

    @property
    def data(self):
        return self.validated_data

    @property
    def errors(self):
        return list(self.itererrors())

    def itererrors(self):
        if self.error:
            yield self.error

    def flatten(self, delimiter='__'):
        '''Make a version of value suitable to use in flat dictionary
        '''
        yield '', self.validated_data

    @classmethod
    def deepen(cls, flat):
        '''Return a canonical version of a flat representation of value
        '''
        if flat is None:
            return None
        try:
            return flat['']
        except (KeyError, TypeError):
            return None


@procrustes.register()
class Tuple(Base):
    @classmethod
    def configure(cls, *types):
        cls.types = types
        cls.len_types = len(types)
        cls.default_data = []

    def check_data(self):
        if not isinstance(self.raw_data, Iterable):
            raise ValidationError('Must be iterable')
        data = tuple(self.raw_data)
        if len(self.types) != len(data):
            raise ValidationError('Must be iterable of length %i'
                                  % len(self.types))
        instances = [t(value, True) for t, value in zip(self.types, data)]
        return instances

    @property
    def data(self):
        if not self.validated_data:
            return
        return tuple(i.data for i in self.validated_data)

    def itererrors(self):
        if self.error:
            yield self.error
        for value in self.validated_data:
            for error in value.itererrors():
                yield error

    def get_included(self):
        if not self.validated_data:
            return (typ(None, False) for typ in self.types)
        return self.validated_data

    def flatten(self, delimiter='__'):
        data = self.get_included()
        for number, value in enumerate(data):
            for key, data in value.flatten(delimiter):
                tail = delimiter + key if key else ''
                yield str(number) + tail, data

    @classmethod
    def deepen(cls, flat, delimiter='__'):
        collector = {}
        set_nums = set(xrange(cls.len_types))
        for key, flatchild in sorted(group_by_key(flat, delimiter).iteritems()):
            try:
                number = int(key)
            except ValueError:
                continue
            if number > cls.len_types:
                continue
            collector[number] = cls.types[number].deepen(flatchild)
            set_nums.remove(number)
        for i in set_nums: # Add unavailable slots
            collector[i] = None
        return tuple(v for k, v in sorted(collector.items()))


@procrustes.register()
class List(Base):
    @classmethod
    def configure(cls, type):
        cls.type = type
        cls.default_data = []

    def check_data(self):
        if not isinstance(self.raw_data, Iterable):
            raise ValidationError('Must be iterable')
        instances = [self.type(i, True) for i in self.raw_data]
        return instances

    @property
    def data(self):
        if not self.validated_data:
            return
        return [i.data for i in self.validated_data]

    def itererrors(self):
        if self.error:
            yield self.error
        for value in self.validated_data:
            for error in value.itererrors():
                yield error

    def get_included(self):
        if not self.validated_data:
            return [self.type(None, False)]
        return self.validated_data

    def flatten(self, delimiter='__'):
        data = self.get_included()
        for number, value in enumerate(data):
            for key, data in value.flatten(delimiter):
                tail = delimiter + key if key else ''
                yield str(number) + tail, data

    @classmethod
    def deepen(cls, flat, delimiter='__'):
        return [cls.type.deepen(flatchild) for flatchild in
                group_by_key(flat, delimiter).itervalues()]


@procrustes.register()
class Dict(Base):
    @classmethod
    def configure(cls, named_types):
        cls.named_types = named_types
        cls.default_data = {}

    def check_data(self):
        if not isinstance(self.raw_data, dict):
            raise ValidationError('Value must be dict')
        instances = OrderedDict()
        for name, typ in self.named_types.iteritems():
            instances[name] = typ(self.raw_data.get(name), True)
        return instances

    @property
    def data(self):
        if not self.validated_data:
            return
        return dict((name, value.data) for name, value
                    in self.validated_data.iteritems())

    def itererrors(self):
        if self.error:
            yield self.error
        for name, value in self.validated_data.iteritems():
            for error in value.itererrors():
                yield error

    def get_included(self):
        if not self.validated_data:
            return OrderedDict((name, typ(None, False)) for name, typ
                                in self.named_types.iteritems())
        return self.validated_data

    def flatten(self, delimiter='__'):
        data = self.get_included()
        for name, value in data.iteritems():
            for key, data in value.flatten(delimiter):
                tail = delimiter + key if key else ''
                yield name + tail, data

    @classmethod
    def deepen(cls, flat, delimiter='__'):
        result = {}
        grouped = group_by_key(flat, delimiter)
        for name, ftype in cls.named_types.items():
            flatchild = grouped.pop(name, None)
            result[name] = ftype.deepen(flatchild)
        # TODO we may have unmatched data in `grouped`
        return result


@procrustes.register()
class String(Base):
    @classmethod
    def configure(cls, min_length=1, max_length=None, regex=None, regex_msg=None):
        cls.min_length = min_length
        cls.max_length = max_length
        cls.regex = re.compile(regex) if regex is not None else None
        cls.regex_msg = regex_msg if regex_msg else 'Dont match'

    def check_data(self):
        if not isinstance(self.raw_data, (str, unicode)):
            raise ValidationError('Must be str or unicode instance')
        slen = len(self.raw_data)

        if self.min_length is not None and slen < self.min_length:
            raise ValidationError('Must be longer than %i' % self.min_length)
        if self.max_length is not None and slen > self.max_length:
            raise ValidationError('Must be shorter than %i' % self.max_length)
        if self.regex:
            match = self.regex.match(self.raw_data)
            if match is None or match.group()!=self.raw_data:
                raise ValidationError(self.regex_msg)

        return self.raw_data


@procrustes.register()
class Integer(Base):
    @classmethod
    def configure(cls, min=None, max=None):
        cls.min = min
        cls.max = max

    def check_data(self):
        try:
            i = int(self.raw_data)
        except (ValueError, TypeError):
            raise ValidationError('Must be number, not a string')

        if self.min is not None and i < self.min:
            raise ValidationError('Must be larger than %i' % self.min)
        if self.max is not None and i > self.max:
            raise ValidationError('Must be smaller than %i' % self.max)

        return i


@procrustes.register()
class Boolean(Base):
    def check_data(self):
        return bool(self.raw_data)


# nice declarativeness
class DeclarativeMeta(type):
    def __new__(cls, name, bases, attrs):
        fields = OrderedDict()
        for name, attr in list(attrs.iteritems()): # explicit copy
            # isinstance(attr, type) == attr is a class
            if isinstance(attr, type) and issubclass(attr, Base):
                fields[name] = attr
                del attrs[name]
        attrs['named_types'] = fields
        attrs['required'] = attrs.get('required', True)
        attrs['default_data'] = {}
        return type.__new__(cls, name, bases, attrs)


class Declarative(Dict):
    __metaclass__ = DeclarativeMeta


# Helpers
def group_by_key(flat, delimiter='__'):
    if flat is None:
        return {}

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
