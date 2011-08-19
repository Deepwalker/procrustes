# (c) Svarga project under terms of the new BSD license

from functools import partial
from procrustes import validators, widgets, utils
from ordereddict import OrderedDict


# Fields
class FieldMixin(object):
    def configure(self, args, kwargs):
        validators.Base.configure(self, args, kwargs)

        self.widget = kwargs.pop('widget', getattr(self, 'widget', widgets.Base))
        self.prefix = kwargs.pop('prefix', 'form')
        self.field_name = kwargs.pop('field_name', None)
        self.widget_kwargs = utils.pop_prefixed_args(kwargs, 'w_')
        super(FieldMixin, self).configure(args, kwargs)

    def widgets(self, id, delimiter='__', parent=''):
        yield self.widget(data=self.data, id=id, error=self.error,
                          delimiter=delimiter, parent=parent,
                          label_name=self.field_name,
                          **self.widget_kwargs)

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
    def widgets(self, id='', delimiter='__', parent='', attribute='widgets'):
        prefix = id + delimiter if id else ''
        data = self.get_included()
        for num, field in enumerate(data):
            if not hasattr(field, attribute):
                continue
            for widget in getattr(field, attribute)(prefix + str(num),
                                                    delimiter, parent):
                yield widget

    def template_widgets(self, id='', delimiter='__', parent=''):
        return self.widgets(id, delimiter, parent, 'template_widgets')


class Tuple(IterableMixin, FieldMixin, validators.Tuple):
    pass


class List(IterableMixin, FieldMixin, validators.List):
    def widgets(self, id='', delimiter='__', parent=''):
        prefix = id + delimiter if id else ''
        # We mark list by yielding fake widget
        marker = partial(widgets.Marker, id=prefix,
                         parent=parent + id, label_name=self.type.field_name)
        yield marker(marker='place')
        data = self.get_included()
        for num, field in enumerate(data):
            yield marker(marker='start')
            for widget in field.widgets(prefix + str(num), delimiter, parent):
                yield widget
            yield marker(marker='stop')

    def template_widgets(self, id='', delimiter='__', parent=''):
        prefix = id + delimiter if id else ''
        marker = partial(widgets.Marker, id=prefix,
                         parent=parent + id, label_name=self.type.field_name)
        parent = parent + id
        field = self.type(None, False)
        yield marker(marker='start')
        for widget in field.widgets(prefix + '%s', delimiter, parent):
            yield widget
        yield marker(marker='stop')


class Dict(FieldMixin, validators.Dict):
    def widgets(self, id='', delimiter='__', parent='', attribute='widgets'):
        prefix = id + delimiter if id else ''
        data = self.get_included()
        for name, field in data.iteritems():
            if not hasattr(field, attribute):
                continue
            for widget in getattr(field, attribute)(prefix + name,
                                                    delimiter=delimiter,
                                                    parent=parent):
                yield widget

    def template_widgets(self, id='', delimiter='__', parent=''):
        return self.widgets(id, delimiter, parent, 'template_widgets')

    def __getattr__(self, attr):
        if attr not in self.named_types:
            raise AttributeError('Atribute %s does not exist' % attr)
        return self.get_included()[attr]


class String(FieldMixin, validators.String):
    pass


class Integer(FieldMixin, validators.Integer):
    pass


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
