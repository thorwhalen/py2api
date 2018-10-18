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


class PermissibleAttr(object):
    def __init__(self, permissible_attrs=None):
        """
        A class whose objects are callable and play the role of an attribute filter.
        The use of this class is to construct a function that will allow or disallow specific attributes to be
        accessed by an ObjWrap.
        :param permissible_attrs: The specification that determines what attributes are allowed to be accessed.
            Note that specifications must be
            complete (i.e. describing the whole attribute path, not just a subset. For example, if you want
            to have access to this.given.thing you, specifying r"this\.given" won't be enough.
            If you're specifying with a regular expression for example, need to specify
            "this\.given.thing" or "this\.given\..*" (the latter giving access to all children of this.given.).
            Allowed formats:
                a list of patterns to include (most common)
                a re.compiled pattern
                a string (that will be passed on to re.compile()
                a dict with either
                    an "include", pointing to a list of patterns to include
                    an "exclude", pointing to a list of patterns to exclude
        """
        self.permissible_attrs = permissible_attrs
        if not permissible_attrs:  # we don't want to allow any attributes
            permissible_attrs = None
        else:
            if isinstance(permissible_attrs, (list, tuple)):
                permissible_attrs = {'include': permissible_attrs}
            if isinstance(permissible_attrs, dict):
                permissible_attrs = get_pattern_from_attr_permissions_dict(permissible_attrs)
            else:
                permissible_attrs = re.compile(permissible_attrs)
        self.permissible_attr_pattern = permissible_attrs

    def __call__(self, attr):
        return bool(self.permissible_attr_pattern is not None and self.permissible_attr_pattern.match(attr))


def obj_str_from_obj(obj):
    try:
        return obj.__class__.__name__
    except AttributeError:
        return 'obj'


def argname_based_specs_from(specs):
    pass


def get_pattern_from_attr_permissions_dict(attr_permissions):
    """
    Construct a compiled regular expression from a permissions dict containing a list of what to include and exclude.
    Will be used in ObjWrapper if permissible_attr_pattern is a dict.
    Note that the function enforces certain patterns (like inclusions ending with $ unless they end with *, etc.
    What is not checked for is that the "." was meant, or if it was "\." that was meant.
    This shouldn't be a problem in most cases, and hey! It's to the user to know regular expressions!
    :param attr_permissions: A dict of the format {'include': INCLUSION_LIST, 'exclude': EXCLUSION_LIST}.
        Both 'include' and 'exclude' are optional, and their lists can be empty.
    :return: a re.compile object

    >>> attr_permissions = {
    ...     'include': ['i.want.this', 'he.wants.that'],
    ...     'exclude': ['i.want', 'he.wants', 'and.definitely.not.this']
    ... }
    >>> r = get_pattern_from_attr_permissions_dict(attr_permissions)
    >>> test = ['i.want.this', 'i.want.this.too', 'he.wants.that', 'he.wants.that.other.thing',
    ...         'i.want.ice.cream', 'he.wants.me'
    ...        ]
    >>> for t in test:
    ...     print("{}: {}".format(t, bool(r.match(t))))
    i.want.this: True
    i.want.this.too: False
    he.wants.that: True
    he.wants.that.other.thing: False
    i.want.ice.cream: False
    he.wants.me: False
    """

    incls = "|".join(attr_permissions.get('include', []))
    excls = "|".join(attr_permissions.get('exclude', []))

    return re.compile(incls + '(?!%s)' % '|'.join(excls) if excls else '')

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
