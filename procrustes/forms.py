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
        cls.prefix = kwargs.pop('prefix', 'form')
        cls.field_configure(*args, **kwargs)

    @classmethod
    def field_configure(cls, *args, **kwargs):
        pass

    def widgets(self, id):
        yield self.widget(data=self.data, id=id)

    @classmethod
    def unflat(self, flat):
        pos = len(self.prefix) + 2
        flat = dict((key[pos:], value) for key, value in flat.iteritems())
        return self.deepen(flat)


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


@forms.register()
class Integer(FieldMixin, validators.Integer):
    pass


class BaseWidget(object):
    def __init__(self, **kwargs):
        self.data = kwargs.pop('data', None)
        self.prefix = kwargs.pop('prefix', 'form')
        self.id = kwargs.pop('id')
        self.attrs = kwargs

    def render(self):
        data = self.data if self.data else ''
        attrs = ' '.join('%s="%s"' % (name, attr) for name, attr
                                                in self.attrs.iteritems())
        if attrs:
            attrs += ' '
        return '<input id="%s__%s" %svalue="%s">' % (self.prefix, self.id, attrs, data)


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
        Assert(widgets) == ['<input id="form__0" value="">', '<input id="form__1" value="">']

        ft = FT(('kuku', 'kuku'))
        widgets = [widget.render() for widget in ft.widgets()]
        Assert(widgets) == ['<input id="form__0" value="kuku">',
                            '<input id="form__1" value="kuku">']
        #Assert(str.render('strid')) == '<input id="strid" value="kukuku">'
        fl = FL(['kuku', 'dsfasfd', 'xcvxczvx'])
        widgets = [widget.render() for widget in fl.widgets()]
        Assert(widgets) == ['<input id="form__0" value="kuku">',
                            '<input id="form__1" value="dsfasfd">',
                            '<input id="form__2" value="xcvxczvx">']

    @p.test
    def dict_field():
        FD = forms.Dict({'a': forms.String(), 'b': forms.String()})
        fd = FD(None)
        widgets = [widget.render() for widget in fd.widgets()]
        Assert(widgets) == ['<input id="form__a" value="">',
                            '<input id="form__b" value="">']

        fd = FD({'a': 'kuku', 'b': 'may-may'})
        widgets = [widget.render() for widget in fd.widgets()]
        Assert(widgets) == ['<input id="form__a" value="kuku">',
                            '<input id="form__b" value="may-may">']
    
    @p.test
    def flat():
        FL = forms.List(forms.String())
        FD = forms.Dict({'a': forms.String(), 'b': forms.String(), 'c': FL})
        flat = {'form__a': 'kuku', 'form__b': 'may-may', 'form__c__0': 'wer', 'form__c__1': 'kuku'}
        unflat = FD.unflat(flat)
        Assert(unflat) == {'a': 'kuku', 'b': 'may-may', 'c': ['kuku', 'wer']}
        fd = FD(unflat)
        widgets = [widget.render() for widget in fd.widgets()]
        Assert(widgets) == ['<input id="form__a" value="kuku">',
                            '<input id="form__c__0" value="kuku">',
                            '<input id="form__c__1" value="wer">',
                            '<input id="form__b" value="may-may">']


    p.run()
