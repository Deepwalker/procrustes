# (c) Svarga project under terms of the new BSD license

from procrustes import procrustes
from attest import Tests, Assert

p = Tests()

I = procrustes.Integer(max=90, required=False)
S = procrustes.String()


@p.test
def simple():
    """Simple validators."""
    Assert(I(10).validate()) == 10
    Assert(I(None).validate()) == None

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
    Assert(pd.data) == None
    pd = PD({'b': 'kuku', 'c': (None, 'Lorem', 90)})
    Assert(pd.data) == {'a': None, 'c': (None, 'Lorem', 90), 'b': 'kuku'}

@p.test
def flat_bulge():
    PT = procrustes.Tuple(I, S, I)
    PD = procrustes.Dict({'a': I, 'b': S, 'c': PT})
    pd = PD({'b': 'kuku', 'c': (None, 'Lorem', 78)})
    flatten = dict(pd.flatten())
    Assert(flatten) == {'a': None, 'c__2': 78, 'c__1': 'Lorem',
                                                      'c__0': None, 'b': 'kuku'}
    bulged = PD.bulge(flatten)
    Assert(bulged) == {'a': None, 'c': (None, 'Lorem', 78), 'b': 'kuku'}
    pd = PD(bulged)
    Assert(pd.data) == {'a': None, 'c': (None, 'Lorem', 78), 'b': 'kuku'}


if __name__ == '__main__':
    p.run()
