# (c) Svarga project under terms of the new BSD license

from procrustes import procrustes
from procrustes import forms
from attest import Tests, Assert

p = Tests()

I = procrustes.Integer(max=90, required=False)
S = procrustes.String()


@p.test
def simple():
    """Simple validators."""
    Assert(I(10).validate()) == 10
    Assert(I().validate()) == None


@p.test
def simple_tuple():
    """Simple tuple ops"""
    PT = procrustes.Tuple(I, S, I)
    pt = PT([10, 'sdfsdf', 30])
    Assert(pt.data) == (10, 'sdfsdf', 30)


@p.test
def simple_list():
    PL = procrustes.List(I)
    pl = PL(xrange(7))
    Assert(pl.data) == range(7)


@p.test
def simple_dict():
    PD = procrustes.Dict({'a': I, 'b': S})
    pd = PD({'a': None, 'b': 'Lorem Ipsum'})
    Assert(pd.data) == {'a': None, 'b': 'Lorem Ipsum'}

    pd = PD({'b': 'Lorem Ipsum'})
    Assert(pd.data) == {'a': None, 'b': 'Lorem Ipsum'}


@p.test
def tuple_dict():
    PT = procrustes.Tuple(I, S, I)
    PD = procrustes.Dict({'a': I, 'b': S, 'c': PT})
    pd = PD({'b': 'kuku', 'c': (None, 'Lorem', 91)})
    Assert(pd.data) == {'a': None, 'c': (None, 'Lorem', None), 'b': 'kuku'}
    pd = PD({'b': 'kuku', 'c': (None, 'Lorem', 90)})
    Assert(pd.data) == {'a': None, 'c': (None, 'Lorem', 90), 'b': 'kuku'}


@p.test
def flat_deepen():
    PT = procrustes.Tuple(I, S, I)
    PD = procrustes.Dict({'a': I, 'b': S, 'c': PT})
    pd = PD({'b': 'kuku', 'c': (None, 'Lorem', 78)})
    flat = dict(pd.flatten())
    Assert(flat) == {'a': None, 'c__2': 78, 'c__1': 'Lorem',
                     'c__0': None, 'b': 'kuku'}
    flat = {'a': None, 'c__2': 78, 'c__1': 'Lorem', 'b': 'kuku'}
    deep = PD.deepen(flat)
    Assert(deep) == {'a': None, 'c': (None, 'Lorem', 78), 'b': 'kuku'}
    pd = PD(deep)
    Assert(pd.data) == {'a': None, 'c': (None, 'Lorem', 78), 'b': 'kuku'}

@p.test
def empty_flatten():
    I = procrustes.Integer(max=90, required=False)
    S = procrustes.String()
    PL = procrustes.List(I)
    PD = procrustes.Dict({'a': I, 'b': S})
    PT = procrustes.Tuple(I, S, I, PL, PD)

    Assert(dict(PT().flatten())) == {'4__b': None, '4__a': None, '1': None,
                                            '0': None, '2': None, '3__0': None}


@p.test
def declarative():
    class Simple(procrustes.Declarative):
        name = procrustes.String(max_length=5)

    simple = Simple({'name': 'test'})
    Assert(simple.data) == {'name': 'test'}

    fail = Simple({'name': 'qweasd'})
    Assert(fail.data) == {'name': None}
    Assert(fail.errors) == ['Must be shorter than 5']

@p.test
def forms_simple():
    str = forms.String()('kukuku')
    Assert(str.data) == 'kukuku'

    FT = forms.Tuple(forms.String(), forms.String())
    FL = forms.List(forms.String())
    ft = FT()
    widgets = [widget.render() for widget in ft.widgets()]
    Assert(widgets) == ['<input id="form__0" name="form__0" value="">',
                        '<input id="form__1" name="form__1" value="">']

    ft = FT(('kuku', 'kuku'))
    widgets = [widget.render() for widget in ft.widgets()]
    Assert(widgets) == ['<input id="form__0" name="form__0" value="kuku">',
                        '<input id="form__1" name="form__1" value="kuku">']
    fl = FL(['kuku', 'dsfasfd', 'xcvxczvx'])
    widgets = [widget.render() for widget in fl.widgets()]
    Assert(widgets) == ['<input id="form__0" name="form__0" value="kuku">',
                        '<input id="form__1" name="form__1" value="dsfasfd">',
                        '<input id="form__2" name="form__2" value="xcvxczvx">']

@p.test
def forms_dict_field():
    FD = forms.Dict({'a': forms.String(), 'b': forms.String()})
    fd = FD()
    widgets = [widget.render() for widget in fd.widgets()]
    Assert(widgets) == ['<input id="form__a" name="form__a" value="">',
                        '<input id="form__b" name="form__b" value="">']

    fd = FD({'a': 'kuku', 'b': 'may-may'})
    widgets = [widget.render() for widget in fd.widgets()]
    Assert(widgets) == ['<input id="form__a" name="form__a" value="kuku">',
                        '<input id="form__b" name="form__b" value="may-may">']

@p.test
def forms_flat():
    FL = forms.List(forms.String())
    FD = forms.Dict({'a': forms.String(), 'b': forms.String(), 'c': FL})
    flat = {'form__a': 'kuku', 'form__b': 'may-may', 'form__c__0': 'wer', 'form__c__1': 'kuku'}
    unflat = FD.unflat(flat)
    Assert(unflat) == {'a': 'kuku', 'b': 'may-may', 'c': ['kuku', 'wer']}
    fd = FD(unflat)
    widgets = [widget.render() for widget in fd.widgets()]
    Assert(widgets) == ['<input id="form__a" name="form__a" value="kuku">',
                        '<input id="form__c__0" name="form__c__0" value="kuku">',
                        '<input id="form__c__1" name="form__c__1" value="wer">',
                        '<input id="form__b" name="form__b" value="may-may">']


if __name__ == '__main__':
    p.run()
