============
 Procrustes
============

Procrustes is a validation library, suitable for validating user input data,
i.e. web forms or API calls. With procrustes you can validate any structure.

For doing this procrustes has three container classes - Tuple, List and Dict.
Tuple come from FP, has fixed count of elements with fixed types.
List can include any amount of values of one type.
And Dict is a dict.


Procrustes consist of validators and forms. You can use validators without
forms functionality. Forms adds mainly widgets and form data parsing.


Validators
~~~~~~~~~~

Most simple what you can to do with procrustes is build validator and use it:

    >>> from procrustes import validators as v
    >>> two_strings_v = v.Tuple(v.String(), v.String())
    >>> auth = two_strings_v(['login', 'password'])
    >>> auth.data
    ('login', 'password')
    >>> auth.errors
    []
    >>> auth = two_strings_v(['login'])
    >>> auth.data
    >>> auth.errors
    ['Must be iterable of length 2']

We have very powerful `List`:

    >>> list_of_pairs_v = v.List(two_strings_v)
    >>> pairs = list_of_pairs_v([(str(x), str(x)) for x in xrange(10)])
    >>> pairs.data
    [('0', '0'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9')]
    >>> pairs.errors
    []

`List`, `Tuple` and `Dict` are recursive, so you can build any data structure you want.

`Dict` example:

    >>> dict_v = v.Dict({'pair': two_strings_v, 'pairs': list_of_pairs_v})
    >>> data = dict_v({'pair': ['a', 'b'], 'pairs': [['a', 'b'], ['c', 'd']]})
    >>> data.data
    {'pair': ('a', 'b'), 'pairs': [('a', 'b'), ('c', 'd')]}
    >>> data.errors
    []

Validators have `required` keyword argument:

    >>> two_strings_v = v.Tuple(v.String(), v.String(), required=False)
    >>> dict_v = v.Dict({'pair': two_strings_v, 'pairs': list_of_pairs_v})
    >>> data = dict_v({'pairs': [['a', 'b'], ['c', 'd']]})
    >>> data.data
    {'pair': None, 'pairs': [('a', 'b'), ('c', 'd')]}
    >>> data.errors
    []

Flat
~~~~

Procrustes can `flat` data:

    >>> list(data.flatten())
    [('pairs__0__0', 'a'), ('pairs__0__1', 'b'), ('pairs__1__0', 'c'), ('pairs__1__1', 'd')]

And unflat it back:

    >>> dict_v.deepen(dict([('pairs__0__0', 'a'), ('pairs__0__1', 'b'), ('pairs__1__0', 'c'), ('pairs__1__1', 'd')]))
    {'pair': (None, None), 'pairs': [('c', 'd'), ('a', 'b')]}


Forms
~~~~~

Forms derived from validators and implemented as mixins to them. Every Field
can work as form. Your form may consist from one `forms.String()`.
In addition to validators forms adds methods `widgets`, `template_widgets`,
`unflat` and `is_valid`.
