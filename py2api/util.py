from __future__ import division

import json
import re
from inspect import getargspec

from py2api.defaults import DFLT_RESULT_FIELD


def _strigify_val(val):
    """
    Stringify a value. Here stringify means:
        * If it's a string, surround it with double quotes (so '"' + val '"')
        * If it's a callable or a type (class, etc.), then get it's __name__
        * If not, just return "{}".format(val)
    See an example of use in enhanced_docstr function.
    :param val: value to be stringified
    :return:
    """
    if isinstance(val, basestring):
        return repr(val)
    elif hasattr(val, "__name__"):
        return val.__name__
    else:
        return str(val)

def enhanced_docstr(func):
    """
    Returns the string of func.__doc__ where it prepended the function call description
    (i.e. function name, arguments, and default values).
    :param func:
    :return:
    >>> def some_function(x):
    ...     pass
    ...
    >>> class SomeClass(object):
    ...     pass
    ...
    >>> def foo(a, b=3, c='as', d=SomeClass, dd=some_function, ddd=None, *args, **kwargs):
    ...     '''some documentation...'''
    ...     pass
    >>> print(enhanced_docstr(foo))
    foo(a, b=3, c="as", d=SomeClass, dd=some_function, ddd=None, *args, **kwargs)
    some documentation...
    >>>
    """
    argspec = getargspec(func)

    dflts = [_strigify_val(d) for d in argspec.defaults or list()]

    args_strings = list()
    args_strings += argspec.args[:-len(dflts)]
    args_strings += map(lambda x: "{}={}".format(*x),
                        zip(argspec.args[-len(dflts):], dflts))
    if argspec.varargs is not None:
        args_strings += ["*{}".format(argspec.varargs)]
    if argspec.keywords is not None:
        args_strings += ["**{}".format(argspec.keywords)]

    func_spec = "{funcname}({args_strings})".format(
        funcname=func.__name__, args_strings=", ".join(args_strings))

    if func.__doc__ is not None:
        return "\n".join((func_spec, func.__doc__))
    else:
        return func_spec




def obj_str_from_obj(obj):
    try:
        return obj.__class__.__name__
    except AttributeError:
        return 'obj'


def argname_based_specs_from(specs):
    pass


def default_to_jdict(result, result_field=DFLT_RESULT_FIELD):
    if isinstance(result, list):
        return {result_field: result}
    elif isinstance(result, dict) and len(result) > 0:
        first_key, first_val = result.iteritems().next()  # look at the first key to determine what to do with the dict
        if isinstance(first_key, int):
            key_trans = unichr
        else:
            key_trans = lambda x: x
        if isinstance(first_val, dict):
            return {result_field: {key_trans(k): default_to_jdict(v) for k, v in result.iteritems()}}
        else:
            return {key_trans(k): v for k, v in result.iteritems()}
    elif hasattr(result, 'to_json'):
        return json.loads(result.to_json())
    else:
        try:
            return {result_field: result}
        except TypeError:
            if hasattr(result, 'next'):
                return {result_field: list(result)}
            else:
                return {result_field: str(result)}


def get_attr_recursively(obj, attr, default=None):
    try:
        for attr_str in attr.split('.'):
            obj = getattr(obj, attr_str)
        return obj
    except AttributeError:
        return default
