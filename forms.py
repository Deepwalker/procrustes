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
    new_cls.base_field_configure(*args, **kwargs)
    new_cls.configure(*args, **kwargs)
    return new_cls


class FieldMixin(object):
    @classmethod
    def base_field_configure(cls, *args, **kwargs):
        cls.widget = kwargs.pop('widget', BaseWidget)
        cls.field_configure(*args, **kwargs)

    @classmethod
    def field_configure(cls, *args, **kwargs):
        pass

    def widgets(self, id):
        yield self.widget(data=self.data, id=id)


class IterableMixin(object):
    def widgets(self, id=''):
        prefix = id + '__' if id else ''
        data = self.get_included()
        for num, field in enumerate(data):
            for widget in field.widgets(prefix + str(num)):
                yield widget


@forms.register()
class Tuple(IterableMixin, FieldMixin, validators.Tuple):
    pass


@forms.register()
class List(IterableMixin, FieldMixin, validators.List):
    pass


@forms.register()
class Dict(FieldMixin, validators.Dict):
    def widgets(self, id=''):
        prefix = id + '__' if id else ''
        data = self.get_included()
        for name, field in data.iteritems():
            for widget in field.widgets(prefix + name):
                yield widget


@forms.register()
class String(FieldMixin, validators.String):
    pass


class BaseWidget(object):
    def __init__(self, **kwargs):
        self.data = kwargs.pop('data', None)
        self.id = kwargs.get('id')
        self.attrs = kwargs

    def render(self):
        data = self.data if self.data else ''
        attrs = ' '.join('%s="%s"' % (name, attr) for name, attr
                                                in self.attrs.iteritems())
        if attrs:
            attrs += ' '
        return '<input %svalue="%s">' % (attrs, data)


if __name__ == '__main__':
    from attest import Tests, Assert
    p = Tests()

    @p.test
    def simple():
        str = forms.String()('kukuku')
        Assert(str.data) == 'kukuku'

        FT = forms.Tuple(forms.String(), forms.String())
        FL = forms.List(forms.String())
        ft = FT(None)
        widgets = [widget.render() for widget in ft.widgets()]
        Assert(widgets) == ['<input id="0" value="">', '<input id="1" value="">']

        ft = FT(('kuku', 'kuku'))
        widgets = [widget.render() for widget in ft.widgets('form')]
        Assert(widgets) == ['<input id="form__0" value="kuku">',
                            '<input id="form__1" value="kuku">']
        #Assert(str.render('strid')) == '<input id="strid" value="kukuku">'
        fl = FL(['kuku', 'dsfasfd', 'xcvxczvx'])
        widgets = [widget.render() for widget in fl.widgets('form')]
        Assert(widgets) == ['<input id="form__0" value="kuku">',
                            '<input id="form__1" value="dsfasfd">',
                            '<input id="form__2" value="xcvxczvx">']

    @p.test
    def dict_field():
        FD = forms.Dict({'a': forms.String(), 'b': forms.String()})
        fd = FD(None)
        widgets = [widget.render() for widget in fd.widgets('form')]
        Assert(widgets) == ['<input id="form__a" value="">',
                            '<input id="form__b" value="">']

        fd = FD({'a': 'kuku', 'b': 'may-may'})
        widgets = [widget.render() for widget in fd.widgets('form')]
        Assert(widgets) == ['<input id="form__a" value="kuku">',
                            '<input id="form__b" value="may-may">']

    p.run()
