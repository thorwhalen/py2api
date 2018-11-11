from __future__ import division

import re

from py2api.constants import TRANS_NOT_FOUND, ATTR
from py2api.constants import _ATTR, _ARGNAME, _ELSE
from py2api.py2rest.constants import _ARGS, _JSON, _ROUTE, _SOURCE

DFLT_TRANS = {
    _ARGS: {'type': str}
}


def _preprocess_trans_dict(trans_dict={}):
    trans_dict = dict(trans_dict)

    trans_dict.setdefault(_ARGS, dict())
    trans_dict.setdefault(_JSON, dict())

    return trans_dict

def get_empty_none(o, a, d=None):
    v = getattr(o, a, d)

    if v is None:
        v = d

    return v

def get_request_data_from_source(request, source):
    if source == _JSON:
        return get_empty_none(request, "json", {}).items()
    elif source == _ARGS:
        return get_empty_none(request, "args", {}).items()
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
    ...         self.url = None
    ...         self.set_url(url)
    ...         if json is None:
    ...             json = {}
    ...         self.json = json
    ...     def set_url(self, url):
    ...         self.url = url
    ...         if self.url is not None:
    ...             self.args = dict(parse_qsl(urlsplit(url).query))
    ...         else:
    ...             self.args = dict()
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
    >>> url = '?attr=any_attr&g=1.61&e=2.17&pi=3.14&x=something_else'
    >>>
    >>> print(input_trans(request=MockRequest(url)))
    ('any_attr', {'x': 'something_else', 'pi': 3, 'e': '2.17', 'g': 1.61})
    >>>
    >>> request = MockRequest(url='?attr=special_attr&g=1.61&e=2.17&pi=3.14')
    >>> print(input_trans(request))
    ('special_attr', {'pi': 3, 'e': set(['1', '2', '7', '.']), 'g': ['1', '.', '6', '1']})
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
    ...     pprint(kwargs)
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
    >>> request.set_url('?attr=special_attr&int_1=34&float_1=3.14159')
    >>> test_item(input_trans, request=request)
    Testing with special_attr
    {'float_1': 3,
     'int_1': 34,
     'list_1': "['should', 'become', 'set']",
     'list_2': 'should|become|tuple'}
    >>> request.set_url('?attr=any_attr&int_1=34&float_1=3.14159')
    >>> test_item(input_trans, request=request)
    Testing with any_attr
    {'float_1': 3.14159,
     'int_1': 34,
     'list_1': set(['become', 'set', 'should']),
     'list_2': ('should', 'become', 'tuple')}
    >>> request = MockRequest(
    ...     url='?attr=any_attr&float_1=3.14159&list_2=should|become|tuple',
    ...     json={
    ...         'list_1': ['should', 'become', 'set'],
    ...         'other_arg': 'another arg'
    ...     }
    ... )
    >>>
    >>> test_item(input_trans, request=request)
    Testing with any_attr
    {'float_1': 3.14159,
     'list_1': set(['become', 'set', 'should']),
     'list_2': ('should', 'become', 'tuple'),
     'other_arg': 'another arg'}
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
    >>> test_item(input_trans, request=request)
    Testing with any_attr
    {'float_1': 2.71,
     'int_1': 34,
     'list_1': set(['become', 'set', 'should']),
     'list_2': ('should', 'become', 'tuple'),
     'other_arg': 'another arg'}
    """

    def __init__(self, trans_spec=None, dflt_spec=None, sources=(_JSON, _ARGS, _ROUTE)):
        if trans_spec is None:
            trans_spec = {}
        if dflt_spec is None:
            dflt_spec = {}
        self.trans_spec = trans_spec
        self.dflt_spec = dflt_spec
        self.sources = sources

    @classmethod
    def from_argname_trans_dict(cls, argname_trans_dict):
        return cls(trans_spec={_ARGNAME: argname_trans_dict})

    def search_trans_func(self, attr, argname, val, trans_spec, source=None):
        trans_func = TRANS_NOT_FOUND  # fallback default (i.e. "found nothing")
        if callable(trans_spec):
            return trans_spec
        elif isinstance(trans_spec, dict):
            if len(trans_spec) == 0:
                return TRANS_NOT_FOUND
            elif len(trans_spec) > 0:

                def search_in_field(trans_spec, field, field_val):
                    trans_func = TRANS_NOT_FOUND
                    _trans_spec = trans_spec.get(field, {}).get(field_val, TRANS_NOT_FOUND)
                    if _trans_spec:
                        trans_func = self.search_trans_func(attr, argname, val, trans_spec=_trans_spec, source=source)

                    return trans_func

                ############### search _SOURCE ###############
                # TODO: Would like to include as search_in_field(trans_spec, _SOURCE, source) in the or below.
                if source is not None:  # only do this if there's an actual source specified
                    _trans_spec = trans_spec.get(_SOURCE, {}).get(source, {})
                    if _trans_spec:
                        trans_func = self.search_trans_func(attr, argname, val, trans_spec=_trans_spec, source=source)

                    if trans_func is not TRANS_NOT_FOUND:
                        return trans_func

                trans_func = \
                    search_in_field(trans_spec, _ATTR, attr) \
                    or search_in_field(trans_spec, _ARGNAME, argname)

                # ############### search _SOURCE ###############
                # if source is not None:  # only do this if there's an actual source specified
                #     _trans_spec = trans_spec.get(_SOURCE, {}).get(source, {})
                #     if _trans_spec:
                #         trans_func = self.search_trans_func(attr, argname, val, trans_spec=_trans_spec, source=source)
                #
                #     if trans_func is not TRANS_NOT_FOUND:
                #         return trans_func
                #
                # ############### search _ATTR ###############
                # _trans_spec = trans_spec.get(_ATTR, {}).get(attr, {})
                # if _trans_spec:
                #     trans_func = self.search_trans_func(attr, argname, val,
                #                                         trans_spec=_trans_spec,
                #                                         source=source)
                #
                # if trans_func is not TRANS_NOT_FOUND:
                #     return trans_func
                #
                # ############### search _ARGNAME ###############
                # _trans_spec = trans_spec.get(_ARGNAME, {}).get(argname, TRANS_NOT_FOUND)
                # if _trans_spec:
                #     trans_func = self.search_trans_func(attr, argname, val,
                #                                         trans_spec=_trans_spec,
                #                                         source=source)
                # if trans_func is not TRANS_NOT_FOUND:
                #     return trans_func

                ############### _ELSE ###############
                _trans_spec = trans_spec.get(_ELSE, TRANS_NOT_FOUND)
                if _trans_spec:
                    trans_func = self.search_trans_func(attr, argname, val,
                                                        trans_spec=_trans_spec,
                                                        source=source)
                if trans_func is not TRANS_NOT_FOUND:
                    return trans_func
                else:
                    return TRANS_NOT_FOUND
                    # if _ELSE in trans_spec:
                    #     return self.search_trans_func(attr, argname, val, trans_spec[_ELSE], source=source)
                    # else:
                    #     return TRANS_NOT_FOUND
        else:
            return TRANS_NOT_FOUND

    def _get_attr_from_request(self, request, **route_args):
        if ATTR in route_args:
            return route_args[ATTR]

        return request.args[ATTR]

    def __call__(self, request, **route_args):
        """
        Extract data to call it with (converting the request data for the given attribute
        (including defaults if any are specified)
        :param request: A flask Request object
        :return: input_dict, where input_dict is an {arg: val, ...} dict
        """
        # get the attr from the request

        attr = self._get_attr_from_request(request)

        # start with specific defaults for that attr, if it exist, or an empty dict if not
        input_dict = self.dflt_spec.get(attr, {})

        for source in self.sources:  # loop through sources
            if source == _ROUTE:
                request_data = route_args
            else:
                request_data = get_request_data_from_source(request, source)  # get the data (dict) of this source
            for argname, val in request_data:  # loop through the (arg, val) pairs of this data...
                if argname == ATTR:
                    continue
                # ... and see if there's a trans_func to convert the val
                trans_func = self.search_trans_func(attr, argname, val, trans_spec=self.trans_spec, source=source)
                if trans_func is not TRANS_NOT_FOUND:  # if there is...
                    input_dict[argname] = trans_func(val)  # ... convert the val
                else:  # if there's not...
                    input_dict[argname] = val  # ... just take the val as is

        input_dict.pop(ATTR, None)  # in case ATTR was in input_dict, remove it.

        return attr, input_dict


re_type = type(re.compile('.'))


class InputTransWithAttrInURL(InputTrans):
    """
    Version of (py2rest) InputTrans that gets its attr from the url itself.
    """
    def __init__(self, trans_spec=None, dflt_spec=None, sources=(_JSON, _ARGS, _ROUTE), attr_from_url='(\w+)$'):
        super(InputTransWithAttrInURL, self).__init__(trans_spec=trans_spec, dflt_spec=dflt_spec, sources=sources)
        if not callable(attr_from_url):
            if isinstance(attr_from_url, basestring):
                _attr_from_url = re.compile(attr_from_url)
            elif isinstance(attr_from_url, re_type):
                _attr_from_url = attr_from_url
            else:
                raise TypeError("attr_from_url must be a callable or a (token matching) regular expression.")

            def __attr_from_url(url):
                m = _attr_from_url.search(url)
                if m:
                    return m.group(1)
                else:
                    raise ValueError("Couldn't parse out an attr from this url: {}".format(url))

            self.attr_from_url = __attr_from_url
        else:
            self.attr_from_url = attr_from_url

    def _get_attr_from_request(self, request):
        return self.attr_from_url(request.url)
