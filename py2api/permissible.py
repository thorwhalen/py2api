# -*- coding: utf-8

"""The attribute filter decorator."""

import re
from collections import defaultdict

try:
    basestring
except:
    basestring = str

class MatchAttr(object):
    """A callable that will match an attribute pattern."""

    _matches_ = defaultdict(dict)

    _re_type_ = type(re.compile(''))

    __slots__ = ["_at"]

    def __new__(cls, attr, *args, **kwargs):
        """If this is already a MatchAttr, return it. Otherwise, create one.

        - If attr is an instance of cls, return it.
        - If attr is a string, create a new instance of cls and
          return it.
        - If attr is an instance of a different MatchAttr, use its
          regular expression to find or create a new cls."""

        if isinstance(attr, cls):
            return attr

        if isinstance(attr, basestring):
            r = re.compile(attr)
        elif isinstance(attr, cls._re_type_):
            r = attr
        elif hasattr(attr, "_at"):
            r = attr._at
        else:
            raise TypeError("%s called with invalid attr: %s" % (cls, attr))

        if r not in cls._matches_[cls]:
            cls._matches_[cls][r] = object.__new__(cls)

        return cls._matches_[cls][r]

    def __init__(self, attr):
        if hasattr(self, "_at"):
            return

        if isinstance(attr, basestring):
            self._at = re.compile(attr)
        else:
            self._at = attr

    def __eq__(self, attr):
        if isinstance(attr, MatchAttr):
            return self._at == attr._at
        elif isinstance(attr, basestring):
            return self._at == re.compile(attr)
        else:
            return self._at == attr

    def __call__(self, attr):
        if self._at.match(attr):
            return True
        else:
            return False

class PermitAttr(MatchAttr):
    """Permits attributes matching our pattern."""

    pass

class DenyAttr(MatchAttr):
    """Denies attributes matching our pattern."""

    def __call__(self, attr):
        """Inverts the match of our pattern."""

        return not super(DenyAttr, self).__call__(attr)

def get_pattern_from_attr_permissions_dict(attr_permissions):
    """
    Construct a compiled regular expression from a permissions dict containing a list of what to include and exclude.
    Will be used in ObjWrapper if permissible_attr_pattern is a dict.

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

    return re.compile(incls), re.compile(excls)
