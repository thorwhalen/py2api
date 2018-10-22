# -*- coding: utf-8

"""The attribute filter decorator."""

import re
try:
    basestring
except:
    basestring = str

class PermissibleAttr(object):
    def __init__(self, permissible_attrs=None):
        """A class whose objects are callable and play the role of an
        attribute filter.

        The use of this class is to construct a function that will
        allow or disallow specific attributes to be accessed by
        an ObjWrap.

        :param permissible_attrs: The specification that determines
                                  what attributes are allowed to be
                                  accessed.

                                  Note that specifications must be
                                  complete (i.e. describing the whole
                                  attribute path, not just a subset.
                                  For example, if you want to have
                                  access to this.given.thing you,
                                  specifying r"this\.given" won't be
                                  enough. If you're specifying with
                                  a regular expression for example,
                                  need to specify r"this\.given.thing"
                                  or r"this\.given\..*" (the latter
                                  giving access to all children of
                                  this.given.).
            Allowed formats:
                a list of patterns to include (most common)
                a re.compiled pattern
                a string (that will be passed on to re.compile()
                a dict with either
                    an "include", pointing to a list of patterns to include
                    an "exclude", pointing to a list of patterns to exclude
        """

        if isinstance(permissible_attrs, (list, tuple)):

            permissible_attrs = {'include': permissible_attrs}
        elif isinstance(permissible_attrs, dict):
            permissible_attrs = get_pattern_from_attr_permissions_dict(permissible_attrs)
        elif permissible_attrs is not None:
            permissible_attrs = re.compile(permissible_attrs)
        self.permissible_attr_pattern = permissible_attrs

    def __call__(self, attr):
        return bool(self.permissible_attr_pattern is not None and self.permissible_attr_pattern.match(attr))

class MatchAttr(object):
    """A callable that will match an attribute pattern."""

    _matches_ = {}

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

        k = (attr, r)

        if k not in cls._matches_:
            cls._matches_[k] = object.__new__(cls)

        return cls._matches_[k]

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
        else:
            return self._at == attr

    def __call__(self, attr):
        if self._at.match(attr):
            return True
        else:
            return False


def get_pattern_from_attr_permissions_dict(attr_permissions):
    """
    Construct a compiled regular expression from a permissions dict containing a list of what to include and exclude.
    Will be used in ObjWrapper if permissible_attr_pattern is a dict.
    Note that the function enforces certain patterns (like inclusions ending with $ unless they end with *, etc.
    What is not checked for is that the "." was meant, or if it was r"\." that was meant.
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

    return re.compile(incls), re.compile(excls)
