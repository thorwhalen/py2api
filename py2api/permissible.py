# -*- coding: utf-8

"""The attribute filter decorator."""

import re
from collections import defaultdict
from functools import wraps

try:
    basestring
except:
    basestring = str

__all__ = ["PermissionDeniedError", "PermitAttr", "DenyAttr", "AttributeFilter"]

class PermissionDeniedError(Exception):
    """Attribute access was forbidden."""

    def __init__(self, o, a, *args, **kwargs):
        super(PermissionDeniedError, self).__init__(*args, **kwargs)

        self.obj = o
        self.attr = a

    def __str__(self):
        return "PermissionDeniedError: %s.%s" % (str(self.obj), self.attr)

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

    @classmethod
    def all(cls):
        return cls("^.*$")

    def __call__(self, attr):
        """Inverts the match of our pattern."""

        return not super(DenyAttr, self).__call__(attr)

class AttributeFilter(object):
    """Filter calls by attribute name.

    This will process a collection of attribute filters."""

    __slots__ = ["_filts"]

    def __init__(self, filters=(DenyAttr.all(),), allow=(), deny=()):
        """Configures an AttributeFilter with the specified filters.

        If allow and deny are both empty, this will use the filters
        instead, which must all be instances of MatchAttr. Otherwise,
        PermitAttr and DenyAttr instances are created from the allow and
        deny lists.
        """

        if allow or deny:
            self._filts = [PermitAttr(a) for a in allow] + [DenyAttr(a) for a in deny]
        else:
            self._filts = list(filters)

    def __call__(self, f):
        """Decorate a method to filter access based on attribute name.

        This can wrap __getattr__ to protect or expose attribute access.."""

        @wraps(f)
        def g(obj, attr):
            if all(t(attr) for t in self._filts):
                return f(obj, attr)
            else:
                raise PermissionDeniedError(obj, attr)

        return g

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
