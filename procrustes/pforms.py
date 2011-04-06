# (c) Svarga project under terms of the new BSD license

from functools import partial
from procrustes import validators, widgets
from ordereddict import OrderedDict


class Forms(object):
    counter = 0

    def __init__(self):
        self.fields = {}

    def __getattr__(self, field):
        if field in self.fields:
            return partial(create_field, field)
        raise AttributeError(field)

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
    new_cls.order_counter = Forms.counter
    Forms.counter += 1
    new_cls.required = kwargs.pop('required', True)
    new_cls.base_field_configure(args, kwargs)
    new_cls.configure(*args, **kwargs)
    return new_cls


# Fields
class FieldMixin(object):
    @classmethod
    def base_field_configure(cls, args, kwargs):
        cls.widget = kwargs.pop('widget', getattr(cls, 'widget', widgets.Base))
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

    def template_widgets(self, id='', delimiter='__'):
        prefix = id + delimiter if id else ''
        data = self.get_included()
        for num, field in enumerate(data):
            if not hasattr(field, 'template_widgets'):
                continue
            for widget in field.template_widgets(prefix + str(num),
                                                 delimiter=delimiter):
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

    def template_widgets(self, id='', delimiter='__'):
        prefix = id + delimiter if id else ''
        data = self.get_included()
        for name, field in data.iteritems():
            if not hasattr(field, 'template_widgets'):
                continue
            for widget in field.template_widgets(prefix + name,
                                                 delimiter=delimiter):
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


@forms.register()
class Boolean(FieldMixin, validators.Boolean):
    widget = widgets.CheckBox


# Declarative
class DeclarativeFieldMeta(validators.DeclarativeMeta):
    def __new__(cls, name, bases, attrs):
        attrs['prefix'] = attrs.get('prefix', 'form')
        attrs = OrderedDict(
                    sorted([(k, v) for k, v in attrs.iteritems()],
                        cmp=lambda x, y: cmp(getattr(x[1], 'order_counter', None),
                                             getattr(y[1], 'order_counter', None))
                        )
                    )
        return validators.DeclarativeMeta.__new__(cls, name, bases, attrs)


class Declarative(Dict):
    __metaclass__ = DeclarativeFieldMeta

forms.Declarative = Declarative
