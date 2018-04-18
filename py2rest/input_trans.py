from __future__ import division

from py2api.constants import TRANS_NOT_FOUND
from py2api.constants import _ATTR, _ARGNAME, _VALTYPE, _ELSE
from py2api.py2rest.constants import _ARGS, _JSON, _SOURCE

DFLT_TRANS = {
    _ARGS: {'type': str}
}


def _preprocess_trans_dict(trans_dict):
    if trans_dict is None:
        trans_dict = dict()
    assert isinstance(trans_dict, dict), "trans_dict must be a dict"
    if _ARGS not in trans_dict:
        trans_dict['_arg'] = dict()
    if _JSON not in trans_dict:
        trans_dict['_json'] = dict()
    return trans_dict


def get_request_data_from_source(request, source):
    if source == _JSON:
        return request.json.items()
    elif source == _ARGS:
        return request.args.items()
    else:
        raise ValueError("This source isn't recognized: {}".format(source))


class InputTrans(object):
    """
    InputTrans allows to flexibly define a callable object to convert arguments into the types expected by the
    attribute that will be called.

    The objective is to transform a flask request into a dict that contains arguments that can be understood by the
    function or method the attribute points to. Therefore it does two things:
    (1) Collect argument names and values from the request object
    (2) Transform/convert/cast the argument values to values the function or method expects
    (3) Adding arguments that haven't been specified, along with default values

    Everything is defined by a trans_spec parameter, which is either
        * a callable (converter function that will be applied to an argument value), or
        * a dict with one or more of the following fields:
            '_source': {source: trans_spec, ...} dict,
            '_attr': {attr: trans_spec} dict
            '_argname': {argname: trans_spec, ...} dict,
            '_valtype': {valtype: trans_spec, ...} dict,
            '_else': trans_spec
    See that this specification language is defined recursively since every trans_spec mentioned above could be itself
    a callable or a trans_spec dict.

    The way it works is that when we ask for the {arg: val, ...} data for a given (attr, request) pair, for each
    (source, attr, argname, val) tuple extracted from request (where source denotes where the data was extracted (e.g.
    from request.args or request.json)), we look for a match in a depth-first search in the trans_spec, in the order
    specified above. That is:
        * We first look to see if there's any particular instructions for the source in question, if we find nothing...
        * we see if the attr is mentioned in the _attr keys, and if we find nothing...
        * we see if the argument name is mentioned in the _argname keys, and if we find nothing...
        * we see if the type of val is mentioned in the _valtype keys (using isinstance(val, valtype), and if not...
        * if there's an else, we look in there, and if there was no else, or still didn't find anything
        * we don't convert the argument's value at all.
    By "find nothing", we mean "find a callable".

    Note that you only need to specify those cases that need special treatment. For example, if your attr (function)
    expects a string argument, and your request represents this argument as a string (which is always the case if
    it's in the url), then there is no need to mention that argument at all.

    Further, if you use the same argument name and type to represent the same "thing", no matter what the attribute
    (which, by the way, is good practice), then you only need to specify an _argname: trans_func once (unless the
    type of the argument will be different according to the source (e.g. url query (args) or json payload).

    Other important note: The top level _valtype and _else were included for consistency and completeness,
    but rare are the cases that they'd actually be included in the specification, and if used, should be used with care.
    An _else at the top level will result in all arguments that were not resolved by _attr, _argname, or _valtype, to be
    cast to the same single type.
    Similarly, a _valtype at the top level will result in all arguments that were not resolved by _attr or _argname to
    be cast a type that is only conditioned by the VALTYPE of the argument.

    Additionally, the class provides two other parameters:
        * dflt_spec: A {attr: {argname: val, ...}, ...} dict that allows us to overwrite the functions defaults, or
            include defaults that are not even in the function.
        * sources: A tuple of sources that InputTrans should extract from the request, and in which order. This is
            might be used to force only specific sources to be used, or which sources should have the priority.
             For priority, the last source mentioned has priority. That is, if sources=('_json', '_args'), which is the
             default, this means that if an argument is mentioned both in request.json and request.args, it is the
             one in request.args that will be taken.

    >>> from urlparse import parse_qsl, urlsplit
    >>> class MockRequest(object):  # a class to mockup a web service request
    ...     def __init__(self, url=None, json=None):
    ...         self.url = url
    ...         self.args = dict(parse_qsl(urlsplit(url).query))
    ...         if json is None:
    ...             json = {}
    ...         self.json = json
    ...
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
    >>> url = '?g=1.61&e=2.17&pi=3.14&x=something_else'
    >>>
    >>> print(input_trans(attr='any_attr', request=MockRequest(url)))
    {'x': 'something_else', 'pi': 3, 'e': '2.17', 'g': 1.61}
    >>>
    >>> request = MockRequest(url='?g=1.61&e=2.17&pi=3.14')
    >>> print(input_trans(attr='special_attr', request=MockRequest(url)))
    {'x': 'something_else', 'pi': 3, 'e': set(['1', '2', '7', '.']), 'g': ['1', '.', '6', '1']}
    >>>
    >>> ####### And now, a more complicated example #############
    >>> # The following more complicated example demonstrates how one can
    >>> #   * condition the conversion on the source (whether it's from request.args (url query) or request.json)
    >>> #   * condition the conversion on the val type, nested within another condition, or not
    >>> from pprint import pprint
    >>>
    >>> class SpecialType(object):
    ...     def __init__(self, x):
    ...         self.x = x
    ...     def __str__(self):
    ...         return str(self.x)
    ...     def __len__(self):
    ...         return len(self.x)
    ...
    >>> def test_item(input_trans, attr, request):
    ...     print("Testing with {}".format(attr))
    ...     pprint(input_trans(attr=attr, request=request))
    ...
    >>> trans_spec = {
    ...     _ATTR: {
    ...         'special_attr': {
    ...             _ARGNAME: {
    ...                 'list_1': str,
    ...                 'list_2': lambda x: '|'.join(x),
    ...                 'float_1': lambda x: int(float(x))
    ...             },
    ...             _VALTYPE: {
    ...                 SpecialType: len
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
    ...     },
    ...     _VALTYPE: {
    ...         # note that such blanket type conditions are rare. They are useful mostly for custom objects.
    ...         SpecialType: str
    ...     }
    ... }
    >>> input_trans = InputTrans(trans_spec=trans_spec)
    >>> request = MockRequest(
    ...     url='?int_1=34&float_1=3.14159',
    ...     json={
    ...         'list_1': ['should', 'become', 'set'],
    ...         'list_2': ['should', 'become', 'tuple'],
    ...         'special': SpecialType("I'm special")
    ...     }
    ... )
    >>> test_item(input_trans, attr='special_attr', request=request)
    Testing with special_attr
    {'float_1': 3,
     'int_1': 34,
     'list_1': "['should', 'become', 'set']",
     'list_2': 'should|become|tuple',
     'special': 11}
    >>> test_item(input_trans, attr='any_attr', request=request)
    Testing with any_attr
    {'float_1': 3.14159,
     'int_1': 34,
     'list_1': set(['become', 'set', 'should']),
     'list_2': ('should', 'become', 'tuple'),
     'special': "I'm special"}
    >>> request = MockRequest(
    ...     url='?int_1=34&float_1=3.14159&list_2=should|become|tuple',
    ...     json={
    ...         'list_1': ['should', 'become', 'set'],
    ...         'other_arg': 'another arg',
    ...         'special': SpecialType("I'm special")
    ...     }
    ... )
    >>>
    >>> test_item(input_trans, attr='any_attr', request=request)
    Testing with any_attr
    {'float_1': 3.14159,
     'int_1': 34,
     'list_1': set(['become', 'set', 'should']),
     'list_2': ('should', 'become', 'tuple'),
     'other_arg': 'another arg',
     'special': "I'm special"}
    >>>
    >>> request = MockRequest(
    ...     url='?int_1=34&float_1=2.71',
    ...     json={
    ...         'list_1': ['should', 'become', 'set'],
    ...         'list_2': ['should', 'become', 'tuple'],
    ...         'other_arg': 'another arg',
    ...         'float_1': 3.14159,
    ...         'special': SpecialType("I'm special")
    ...     }
    ... )
    >>> test_item(input_trans, attr='any_attr', request=request)
    Testing with any_attr
    {'float_1': 2.71,
     'int_1': 34,
     'list_1': set(['become', 'set', 'should']),
     'list_2': ('should', 'become', 'tuple'),
     'other_arg': 'another arg',
     'special': "I'm special"}
    """

    def __init__(self, trans_spec=None, dflt_spec=None, sources=(_JSON, _ARGS)):
        if trans_spec is None:
            trans_spec = {}
        if dflt_spec is None:
            dflt_spec = {}
        self.trans_spec = trans_spec
        self.dflt_spec = dflt_spec
        self.sources = sources

    def _get_val_from_arg(self, arg, attr):
        pass

    def search_trans_func(self, attr, argname, val, trans_spec, source=None):
        trans_func = TRANS_NOT_FOUND  # fallback default (i.e. "found nothing")
        # print('search_trans_func: {}'.format(trans_spec))
        if callable(trans_spec):
            # print("  callable(trans_spec)")
            return trans_spec
        elif isinstance(trans_spec, dict):
            if len(trans_spec) == 0:
                # print("  len(trans_spec) == 0")
                return TRANS_NOT_FOUND
            elif len(trans_spec) > 0:
                ############### search _SOURCE ###############
                if source is not None:  # only do this if there's an actual source specified
                    _trans_spec = trans_spec.get(_SOURCE, {}).get(source, {})
                    if _trans_spec:
                        trans_func = self.search_trans_func(attr, argname, val, trans_spec=_trans_spec, source=source)

                    if trans_func is not TRANS_NOT_FOUND:
                        # print("  _SOURCE trans_func")
                        return trans_func

                ############### search _ATTR ###############
                # print('  _ATTR: search_trans_func({},{},{})'.format(attr, argname, val))
                _trans_spec = trans_spec.get(_ATTR, {}).get(attr, {})
                if _trans_spec:
                    trans_func = self.search_trans_func(attr, argname, val,
                                                        trans_spec=_trans_spec,
                                                        source=source)

                if trans_func is not TRANS_NOT_FOUND:
                    # print("  _ATTR trans_func")
                    return trans_func

                ############### search _ARGNAME ###############
                # print('  _ARGNAME: search_trans_func({},{},{})'.format(attr, argname, val))
                _trans_spec = trans_spec.get(_ARGNAME, {}).get(argname, TRANS_NOT_FOUND)
                if _trans_spec:
                    trans_func = self.search_trans_func(attr, argname, val,
                                                        trans_spec=_trans_spec,
                                                        source=source)
                if trans_func is not TRANS_NOT_FOUND:
                    # print("  _ARGNAME trans_func")
                    return trans_func

                ############### search _VALTYPE ###############
                if _VALTYPE in trans_spec:
                    for _type, _type_trans_spec in trans_spec[_VALTYPE].items():
                        if isinstance(val, _type):
                            # print("  _VALTYPE trans_func")
                            return _type_trans_spec

                ############### _ELSE ###############
                if _ELSE in trans_spec:
                    # print("  _ELSE search")
                    return self.search_trans_func(attr, argname, val, trans_spec[_ELSE], source=source)
                else:
                    # print("  _ELSE ARG_NOT_FOUND")
                    return TRANS_NOT_FOUND
        else:
            # print("  all else failed ARG_NOT_FOUND")
            return TRANS_NOT_FOUND

    def __call__(self, attr, request):
        """
        Extract and convert the request data for the given attribute (including defaults if any are specified)
        :param attr: The attribute the request is for
        :param request: A flask Request object
        :return: an {arg: val, ...} dict
        """
        # start with the defaults (or an empty dict)
        input_dict = self.dflt_spec.get(attr, {})

        for source in self.sources:  # loop through sources
            request_data = get_request_data_from_source(request, source)  # get the data (dict) of this source
            for argname, val in request_data:  # loop through the (arg, val) pairs of this data...
                # ... and see if there's a trans_func to convert the val
                trans_func = self.search_trans_func(attr, argname, val, trans_spec=self.trans_spec, source=source)
                if trans_func is not TRANS_NOT_FOUND:  # if there is...
                    input_dict[argname] = trans_func(val)  # ... convert the val
                else:  # if there's not...
                    input_dict[argname] = val  # ... just take the val as is

        return input_dict
