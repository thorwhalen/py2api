# py2api.py2rest.input_trans

Input transformation for the REST layer: parse request arguments into the
Python call arguments expected by the wrapped object.

### Functions

| `get_request_data_from_source`(request, source)   |    |
|---------------------------------------------------|----|

### Classes

| [`InputTrans`](#py2api.py2rest.input_trans.InputTrans)([trans_spec, dflt_spec, sources])   | InputTrans allows to flexibly define a callable object to convert arguments into the types expected by the attribute that will be called.   |
|-------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| [`InputTransWithAttrInURL`](#py2api.py2rest.input_trans.InputTransWithAttrInURL)([trans_spec, ...])     | Version of (py2rest) InputTrans that gets its attr from the url itself.                                                                     |

### *class* py2api.py2rest.input_trans.InputTrans(trans_spec=None, dflt_spec=None, sources=('_json', '_args', '_route'))

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

InputTrans allows to flexibly define a callable object to convert arguments into the types expected by the
attribute that will be called.

The objective is to transform a flask request into a dict that contains arguments that can be understood by the
function or method the attribute points to. Therefore it does two things:
(1) Collect argument names and values from the request object
(2) Transform/convert/cast the argument values to values the function or method expects
(3) Adding arguments that haven’t been specified, along with default values

Everything is defined by a trans_spec parameter, which is either

> * a callable (converter function that will be applied to an argument value), or
> * a dict with one or more of the following fields:
>   : ‘_source’: {source: trans_spec, …} dict,
>     ‘_attr’: {attr: trans_spec} dict
>     ‘_argname’: {argname: trans_spec, …} dict,
>     ‘_else’: trans_spec

See that this specification language is defined recursively since every trans_spec mentioned above could be itself
a callable or a trans_spec dict.

The way it works is that when we ask for the {arg: val, …} data for a given (attr, request) pair, for each
(source, attr, argname, val) tuple extracted from request (where source denotes where the data was extracted (e.g.
from request.args or request.json)), we look for a match in a depth-first search in the trans_spec, in the order
specified above. That is:

> * We first look to see if there’s any particular instructions for the source in question, if we find nothing…
> * we see if the attr is mentioned in the \_attr keys, and if we find nothing…
> * we see if the argument name is mentioned in the \_argname keys, and if we find nothing…
> * we see if the type of val is mentioned in the \_valtype keys (using isinstance(val, valtype), and if not…
> * if there’s an else, we look in there, and if there was no else, or still didn’t find anything
> * we don’t convert the argument’s value at all.

By “find nothing”, we mean “find a callable”.

Note that you only need to specify those cases that need special treatment. For example, if your attr (function)
expects a string argument, and your request represents this argument as a string (which is always the case if
it’s in the url), then there is no need to mention that argument at all.

Further, if you use the same argument name and type to represent the same “thing”, no matter what the attribute
(which, by the way, is good practice), then you only need to specify an \_argname: trans_func once (unless the
type of the argument will be different according to the source (e.g. url query (args) or json payload).

Other important note: The top level \_valtype and \_else were included for consistency and completeness,
but rare are the cases that they’d actually be included in the specification, and if used, should be used with care.
An \_else at the top level will result in all arguments that were not resolved by \_attr, \_argname, or \_valtype, to be
cast to the same single type.
Similarly, a \_valtype at the top level will result in all arguments that were not resolved by \_attr or \_argname to
be cast a type that is only conditioned by the VALTYPE of the argument.

Additionally, the class provides two other parameters:

> * dflt_spec: A {attr: {argname: val, …}, …} dict that allows us to overwrite the functions defaults, or
>   : include defaults that are not even in the function.
> * sources: A tuple of sources that InputTrans should extract from the request, and in which order. This is
>   : might be used to force only specific sources to be used, or which sources should have the priority.
>     : For priority, the last source mentioned has priority. That is, if sources=(‘_json’, ‘_args’), which is the
>       default, this means that if an argument is mentioned both in request.json and request.args, it is the
>       one in request.args that will be taken.
```pycon
>>> from urllib.parse import parse_qsl, urlsplit
>>> class MockRequest(object):  # a class to mockup a web service request
...     def __init__(self, url=None, json=None):
...         self.url = url
...         self.json = json or {}
...     @property
...     def args(self):
...         if self.url is not None:
...             return dict(parse_qsl(urlsplit(self.url).query))
...         else:
...             return dict()
>>> # Most of the time, all you'll need is to specify the argnames that need to be converted, plus what ever
>>> # exceptions to this you might have (usually, if the conversion depends on the attribute name).
>>> trans_spec = {
...     _ARGNAME: {
...         'g': float,  # all g should be converted to float (unless... see _ATTR specification)
...         'pi': lambda x: int(float(x)),  # all pi arguments should be converted to int
...     },
...     _ATTR: {
...         'special_attr': {
...             _ARGNAME: {
...                 'g': list,  # if g is an argument of the special_attr function, it should be converted to list
...                 'e': set,  # e argument of special_attr function should be converted to a set
...             }
...         }
...     },  # And that's all. All other arguments should be left alone.
... }
>>> input_trans = InputTrans(trans_spec)
>>> url = '?attr=any_attr&g=1.61&e=2.17&pi=3.14&x=something_else'
>>>
>>> expected = ('any_attr', {'g': 1.61, 'e': '2.17', 'pi': 3, 'x': 'something_else'})
>>> assert input_trans(request=MockRequest(url)) == expected
>>> # ('any_attr', {'g': 1.61, 'e': '2.17', 'pi': 3, 'x': 'something_else'})
>>>
>>> request = MockRequest(url='?attr=special_attr&g=1.61&e=2.17&pi=3.14')
>>> expected = ('special_attr', {'g': ['1', '.', '6', '1'], 'e': {'1', '7', '.', '2'}, 'pi': 3})
>>> assert input_trans(request) == expected
>>> #('special_attr', {'g': ['1', '.', '6', '1'], 'e': {'7', '2', '1', '.'}, 'pi': 3})
>>>
>>> ####### And now, a more complicated example #############
>>> # The following more complicated example demonstrates how one can
>>> #   * condition the conversion on the source (whether it's from request.args (url query) or request.json)
>>> #   * condition the conversion on the val type, nested within another condition, or not
>>> from pprint import pprint
>>>
>>> def test_item(input_trans, request):
...     attr, kwargs = input_trans(request)
...     print("Testing with {}".format(attr))
...     return kwargs
...
>>> trans_spec = {
...     _ATTR: {
...         'special_attr': {
...             _ARGNAME: {
...                 'list_1': str,
...                 'list_2': lambda x: '|'.join(x),
...                 'float_1': lambda x: int(float(x))
...             }
...         }
...     },
...     _ARGNAME: {
...         'list_1': set,
...         'list_2': {
...             _SOURCE: {
...                 _ARGS: lambda x: tuple(x.split('|'))
...             },
...             _ELSE: tuple
...         },
...         'int_1': int,
...         'float_1': float
...     }
... }
>>> input_trans = InputTrans(trans_spec=trans_spec)
>>> request = MockRequest(
...     json={
...         'list_1': ['should', 'become', 'set'],
...         'list_2': ['should', 'become', 'tuple']
...     }
... )
>>> request.url = '?attr=special_attr&int_1=34&float_1=3.14159'
>>> got = test_item(input_trans, request=request)
Testing with special_attr
>>> expected = {'list_1': "['should', 'become', 'set']",
...     'list_2': 'should|become|tuple',
...     'int_1': 34, 'float_1': 3}
>>> assert got == expected
>>>
>>> request.url = '?attr=any_attr&int_1=34&float_1=3.14159'
>>> got = test_item(input_trans, request=request)
Testing with any_attr
>>> expected = {'list_1': {'should', 'become', 'set'},
...     'list_2': ('should', 'become', 'tuple'),
...     'int_1': 34, 'float_1': 3.14159}
>>> assert got == expected
>>>
>>> request = MockRequest(
...     url='?attr=any_attr&float_1=3.14159&list_2=should|become|tuple',
...     json={
...         'list_1': ['should', 'become', 'set'],
...         'other_arg': 'another arg'
...     }
... )
>>>
>>> got = test_item(input_trans, request=request)
Testing with any_attr
>>> expected = {'list_1': {'set', 'should', 'become'},
...         'other_arg': 'another arg',
...         'float_1': 3.14159,
...         'list_2': ('should', 'become', 'tuple')}
>>> assert got == expected
>>>
>>> request = MockRequest(
...     url='?attr=any_attr&int_1=34&float_1=2.71',
...     json={
...         'list_1': ['should', 'become', 'set'],
...         'list_2': ['should', 'become', 'tuple'],
...         'other_arg': 'another arg',
...         'float_1': 3.14159
...     }
... )
>>> got = test_item(input_trans, request=request)
Testing with any_attr
>>> expected = {'list_1': {'should', 'set', 'become'},
...         'list_2': ('should', 'become', 'tuple'),
...         'other_arg': 'another arg',
...         'float_1': 2.71, 'int_1': 34}
>>> assert got == expected
```

### *class* py2api.py2rest.input_trans.InputTransWithAttrInURL(trans_spec=None, dflt_spec=None, sources=('_json', '_args', '_route'), attr_from_url='(\\\\w+)$')

Bases: [`InputTrans`](#py2api.py2rest.input_trans.InputTrans)

Version of (py2rest) InputTrans that gets its attr from the url itself.
