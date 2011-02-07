# (c) Svarga project under terms of the new BSD license

from functools import partial
from procrustes import validators


class Forms(object):
    def __init__(self):
        self.fields = {}

    def __getattr__(self, field):
        if field in self.fields:
            return partial(create_field, field)
        raise AttributeError(validator)

    def register(self, *args):
        largs = len(args)
        def wrapper(field):
            field_name = args[0] if largs else field.__name__
            self.register(field_name, field)
            return field

        if largs==2:
            self.fields[args[0]] = args[1]
        else:
            return wrapper

forms = Forms()


def create_field(field, *args, **kwargs):
    cls = forms.fields[field]
    new_cls = type('Pc' + field, (cls, ), {})
    new_cls.required = kwargs.pop('required', True)
    new_cls.base_field_configure(args, kwargs)
    new_cls.configure(*args, **kwargs)
    return new_cls


# Fields
class FieldMixin(object):
    @classmethod
    def base_field_configure(cls, args, kwargs):
        cls.widget = kwargs.pop('widget', BaseWidget)
        cls.prefix = kwargs.pop('prefix', 'form')
        cls.name = kwargs.pop('name', None)
        cls.field_configure(args, kwargs)

    @classmethod
    def field_configure(cls, args, kwargs):
        pass

    def widgets(self, id, delimiter=None):
        yield self.widget(data=self.data, id=id, error=self.error,
                                                 label_name=self.name)

    @classmethod
    def unflat(self, flat, delimiter='__'):
        pos = len(self.prefix) + 2
        flat = dict((key[pos:], value) for key, value in flat.iteritems())
        return self.deepen(flat, delimiter=delimiter)

    def is_valid(self, delimiter='__'):
        self.raw_data = self.unflat(self.raw_data, delimiter=delimiter)
        self.validate(safe=True)
        if not self.errors:
            return True


class IterableMixin(object):
    def widgets(self, id='', delimiter='__'):
        prefix = id + delimiter if id else ''
        data = self.get_included()
        for num, field in enumerate(data):
            for widget in field.widgets(prefix + str(num), delimiter=delimiter):
                yield widget


@forms.register()
class Tuple(IterableMixin, FieldMixin, validators.Tuple):
    pass


@forms.register()
class List(IterableMixin, FieldMixin, validators.List):
    def template_widgets(self, id='', delimiter='__'):
        prefix = id + delimiter if id else ''
        field = self.type(None, False)
        for widget in field.widgets(prefix + '%s', delimiter=delimiter):
            yield widget


@forms.register()
class Dict(FieldMixin, validators.Dict):
    def widgets(self, id='', delimiter='__'):
        prefix = id + delimiter if id else ''
        data = self.get_included()
        for name, field in data.iteritems():
            for widget in field.widgets(prefix + name, delimiter=delimiter):
                yield widget

    def __getattr__(self, attr):
        if attr not in self.named_types:
            raise AttributeError('Atribute %s does not exist' % attr)
        return self.get_included()[attr]


@forms.register()
class String(FieldMixin, validators.String):
    pass


@forms.register()
class Integer(FieldMixin, validators.Integer):
    pass


# Declarative
class DeclarativeFieldMeta(validators.DeclarativeMeta):
    def __new__(cls, name, bases, attrs):
        attrs['prefix'] = attrs.get('prefix', 'form')
        return validators.DeclarativeMeta.__new__(cls, name, bases, attrs)


class Declarative(Dict):
    __metaclass__ = DeclarativeFieldMeta

forms.Declarative = Declarative


# Widgets
class BaseWidget(object):
    def __init__(self, data=None, prefix='form', id=None, error=None, **kwargs):
        self.data = data
        self.prefix = prefix
        self.id = id
        self.error = error
        self.label_name = kwargs.pop('label_name', None)
        if self.label_name is None:
            self.label_name = self.id
        self.attrs = kwargs

    def render(self):
        data = self.data if self.data else ''
        attrs = ' '.join('%s="%s"' % (name, attr) for name, attr
                                                in self.attrs.iteritems())
        if attrs:
            attrs += ' '
        name = self.prefix + '__' + self.id
        return '<input id="{0}" name="{0}" {1}value="{2}">'.format(name, attrs, data)

    def label(self):
        name = self.prefix + '__' + self.id
        return '<label for="%s">%s</label>' % (name, self.label_name)

