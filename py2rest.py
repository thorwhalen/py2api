"""
Base module to wrap a "controller" class for a web service REST API.

This module is stripped to it's minimal (but still powerful) functionality, containing only two imports from the
Python's (2.7) standard library: re and json, and includes all necessary code in this single .py file.

Many useful utils to extend it's functionality are included elsewhere so as to enable the deployment of
minimum-necessary code, crucial, for instance, for micro-services.
"""

import re
import json

DFLT_LRU_CACHE_SIZE = 20
DFLT_RESULT_FIELD = 'result'


########################################################################################################################
# MAIN
########################################################################################################################

class ObjWrapper(object):
    def __init__(self,
                 obj_constructor,
                 obj_constructor_arg_names=None,  # used to determine the params of the object constructors
                 convert_arg=None,  # input processing: Dict specifying how to prepare ws arguments for methods
                 file_var='file',  # input processing: name of the variable to use if there's a 'file' in request.files
                 permissible_attr_pattern='[^_].*',  # what attributes are allowed to be accessed
                 to_jdict=default_to_jdict,  # output processing: Function to convert an output to a jsonizable dict
                 obj_str='obj',  # name of object to use in error messages
                 cache_size=DFLT_LRU_CACHE_SIZE,
                 debug=0):
        """
        An class to wrap a "controller" class for a web service API.
        It takes care of LRU caching objects constructed before (so they don't need to be re-constructed for every
        API call), and converting request.json and request.args arguments to the types that will be recognized by
        the method calls.
        :param obj_constructor: a function that, given some arguments, constructs an object. It is this object
            that will be wrapped for the webservice
        :param obj_constructor_arg_names:
        :param convert_arg: (processing) a dict keyed by variable names (str) and valued by a dict containing a
            'type': a function (typically int, float, bool, and list) that will convert the value of the variable
                to make it web service compliant
            'default': A value to assign to the variable if it's missing.
        :param The pattern that determines what attributes are allowed to be accessed. Note that patterns must be
            complete patterns (i.e. describing the whole attribute path, not just a subset. For example, if you want
            to have access to this.given.thing you, specifying r"this\.given" won't be enough. You need to specify
            "this\.given.thing" or "this\.given\..*" (the latter giving access to all children of this.given.).
            Allowed formats:
                a re.compiled pattern
                a string (that will be passed on to re.compile()
                a dict with either
                    an "exclude", pointing to a list of patterns to exclude
                    an "include", pointing to a list of patterns to include
        :param to_jdict: (input processing) Function to convert an output to a jsonizable dict
        """
        self.obj_constructor = lru_cache(cache_size=cache_size)(obj_constructor)

        if obj_constructor_arg_names is None:
            obj_constructor_arg_names = []
        elif isinstance(obj_constructor_arg_names, basestring):
            obj_constructor_arg_names = [obj_constructor_arg_names]
        self.obj_constructor_arg_names = obj_constructor_arg_names

        if convert_arg is None:
            convert_arg = {}
        self.convert_arg = convert_arg  # a specification of how to convert specific argument names or types
        self.file_var = file_var

        if isinstance(permissible_attr_pattern, dict):
            self.permissible_attr_pattern = get_pattern_from_attr_permissions_dict(permissible_attr_pattern)
        else:
            self.permissible_attr_pattern = re.compile(permissible_attr_pattern)
        self.to_jdict = to_jdict
        self.obj_str = obj_str
        self.debug = debug

    def _get_kwargs_from_request(self, request):
        """
        Translate the flask request object into a dict, taking first the contents of request.arg,
        converting them to a type if the name is listed in the convert_arg property, and assigning a default value
        (if specified bu convert_arg), and then updating with the contents of request.json
        :param request: the flask request object
        :return: a dict of kwargs corresponding to the union of post and get arguments
        """
        kwargs = extract_kwargs(request, convert_arg=self.convert_arg, file_var=self.file_var)

        return dict(kwargs)

    def _is_permissible_attr(self, attr):
        return bool(self.permissible_attr_pattern.match(attr))

    def obj(self, obj, attr=None, result_field=DFLT_RESULT_FIELD, **method_kwargs):
        # get or make the root object
        if isinstance(obj, dict):
            obj = self.obj_constructor(**obj)
        elif isinstance(obj, (tuple, list)):
            obj = self.obj_constructor(*obj)
        elif obj is not None:
            obj = self.obj_constructor(obj)
        else:
            obj = self.obj_constructor()

        # at this point obj is an actual obj_constructor constructed object....

        # get the leaf object
        if attr is None:
            raise MissingAttribute()
        obj = get_attr_recursively(obj, attr)  # at this point obj is the nested attribute object

        # call a method or return a property
        if callable(obj):
            return self.to_jdict(obj(**method_kwargs), result_field=result_field)
        else:
            return self.to_jdict(obj, result_field=result_field)

    def robj(self, request):
        """
        Translates a request to an object access (get property value or call object method).
            Uses self._get_kwargs_from_request(request) to get a dict of kwargs from request.arg
        (with self.convert_arg conversions)
        and request.json.
            The object to be constructed (or retrieved from cache) is determined by the self.obj_constructor_arg_names
        list. The names listed there will be extracted from the request kwargs and passed on to the object constructor
        (or cache).
            The attribute (property or method) to be accessed is determined by the 'attr' argument, which is a
        period-separated string specifying the path to the attribute (e.g. "this.is.what.i.want" will access
        obj.this.is.what.i.want).
            A requested attribute is first checked against "self._is_permissible_attr" before going further.
        The latter method is used to control access to object attributes.
        :param request: A flask request
        :return: The value of an object's property, or the output of a method.
        """
        kwargs = self._get_kwargs_from_request(request)
        if self.debug > 0:
            print("robj: kwargs = {}".format(kwargs))
        obj_kwargs = {k: kwargs.pop(k) for k in self.obj_constructor_arg_names if k in kwargs}

        attr = kwargs.pop('attr', None)
        if attr is None:
            raise MissingAttribute()
        elif not self._is_permissible_attr(attr):
            print attr
            print str(self.permissible_attr_pattern.pattern)
            raise ForbiddenAttribute(attr)
        if self.debug > 0:
            print("robj: attr={}, obj_kwargs = {}, kwargs = {}".format(attr, obj_kwargs, kwargs))
        return self.obj(obj=obj_kwargs, attr=attr, **kwargs)


########################################################################################################################
# UTILS
########################################################################################################################

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

    s = ""

    # process inclusions
    corrected_list = []
    for include in attr_permissions.get('include', []):
        if not include.endswith('*'):
            if not include.endswith('$'):
                include += '$'
        else:  # ends with "*"
            if include.endswith('\.*'):
                # assume that's not what the user meant, so change
                include = include[:-3] + '.*'
            elif include[-2] != '.':
                # assume that's not what the user meant, so change
                include = include[:-1] + '.*'
        corrected_list.append(include)
    s += '|'.join(corrected_list)

    # process exclusions
    corrected_list = []
    for exclude in attr_permissions.get('exclude', []):
        if not exclude.endswith('$') and not exclude.endswith('*'):
            # add to exclude all subpaths if not explicitly ending with "$"
            exclude += '.*'
        else:  # ends with "*"
            if exclude.endswith('\.*'):
                # assume that's not what the user meant, so change
                exclude = exclude[:-3] + '.*'
            elif exclude[-2] != '.':
                # assume that's not what the user meant, so change
                exclude = exclude[:-1] + '.*'
        corrected_list.append(exclude)
    if corrected_list:
        s += '(?!' + '|'.join(corrected_list) + ')'

    return re.compile(s)


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


def extract_kwargs(request, convert_arg=None, file_var='file'):
    if convert_arg is None:
        convert_arg = {}
    kwargs = dict()
    for k in request.args.keys():
        if k in convert_arg:
            if 'default' in convert_arg[k]:
                kwargs[k] = request.args.get(k,
                                             type=convert_arg[k].get('type', str),
                                             default=convert_arg[k]['default'])
            else:
                kwargs[k] = request.args.get(k, type=convert_arg[k].get('type', str))
        else:
            kwargs[k] = request.args.get(k)
    if request.json is not None:
        kwargs = dict(kwargs, **request.json)
    if 'file' in request.files:
        kwargs[file_var] = request.files['file']
    return kwargs


def get_attr_recursively(obj, attr, default=None):
    try:
        for attr_str in attr.split('.'):
            obj = getattr(obj, attr_str)
        return obj
    except AttributeError:
        return default


def obj_str_from_obj(obj):
    try:
        return obj.__class__.__name__
    except AttributeError:
        return 'obj'


########################################################################################################################
# ERRORS
########################################################################################################################

class ClientError(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


# class EmptyResponse(ClientError):
#     status_code = 400
#
#     def __init__(self, message, payload=None):
#         super(EmptyResponse, self).__init__(message, self.status_code, payload)


class BadRequest(ClientError):
    status_code = 400

    def __init__(self, message, payload=None):
        super(BadRequest, self).__init__(message, self.status_code, payload)


class Forbidden(ClientError):
    status_code = 403

    def __init__(self, message, payload=None):
        super(Forbidden, self).__init__(message, self.status_code, payload)


class ForbiddenAttribute(Forbidden):
    def __init__(self, attr, payload=None):
        super(self.__class__, self).__init__("Forbidden attribute: " + attr, payload)


# class ForbiddenMethod(Forbidden):
#     def __init__(self, method, payload=None):
#         super(self.__class__, self).__init__("Forbidden method: " + method, payload)


class ForbiddenProperty(Forbidden):
    def __init__(self, property, payload=None):
        super(self.__class__, self).__init__("Forbidden property: " + property, payload)


class MissingAttribute(BadRequest):
    def __init__(self, message="No attribute (method or property) was specified.", payload=None):
        super(self.__class__, self).__init__(message, payload)


########################################################################################################################
# LRU
########################################################################################################################

from collections import namedtuple
from functools import update_wrapper
from threading import RLock

_CacheInfo = namedtuple("CacheInfo", ["hits", "misses", "maxsize", "currsize"])

"""
lru_cache is now built in of Python 3. This is a back-port of it found online.
Can't find the original author since it seems so many poeple copied and reused this code when searching for it online
"""


class _HashedSeq(list):
    __slots__ = 'hashvalue'

    def __init__(self, tup, hash=hash):
        self[:] = tup
        self.hashvalue = hash(tup)

    def __hash__(self):
        return self.hashvalue


def _make_key(args, kwds, typed,
              kwd_mark=(object(),),
              fasttypes={int, str, frozenset, type(None)},
              sorted=sorted, tuple=tuple, type=type, len=len):
    'Make a cache key from optionally typed positional and keyword arguments'
    key = args
    if kwds:
        sorted_items = sorted(kwds.items())
        key += kwd_mark
        for item in sorted_items:
            key += item
    if typed:
        key += tuple(type(v) for v in args)
        if kwds:
            key += tuple(type(v) for k, v in sorted_items)
    elif len(key) == 1 and type(key[0]) in fasttypes:
        return key[0]
    return _HashedSeq(key)


def lru_cache(cache_size=DFLT_LRU_CACHE_SIZE, typed=False):
    """Least-recently-used cache decorator.

    If *maxsize* is set to None, the LRU features are disabled and the cache
    can grow without bound.

    If *typed* is True, arguments of different types will be cached separately.
    For example, f(3.0) and f(3) will be treated as distinct calls with
    distinct results.

    Arguments to the cached function must be hashable.

    View the cache statistics named tuple (hits, misses, maxsize, currsize) with
    f.cache_info().  Clear the cache and statistics with f.cache_clear().
    Access the underlying function with f.__wrapped__.

    See:  http://en.wikipedia.org/wiki/Cache_algorithms#Least_Recently_Used

    """

    # Users should only access the lru_cache through its public API:
    #       cache_info, cache_clear, and f.__wrapped__
    # The internals of the lru_cache are encapsulated for thread safety and
    # to allow the implementation to change (including a possible C version).

    def decorating_function(user_function):

        cache = dict()
        stats = [0, 0]  # make statistics updateable non-locally
        HITS, MISSES = 0, 1  # names for the stats fields
        make_key = _make_key
        cache_get = cache.get  # bound method to lookup key or return None
        _len = len  # localize the global len() function
        lock = RLock()  # because linkedlist updates aren't threadsafe
        root = []  # root of the circular doubly linked list
        root[:] = [root, root, None, None]  # initialize by pointing to self
        nonlocal_root = [root]  # make updateable non-locally
        PREV, NEXT, KEY, RESULT = 0, 1, 2, 3  # names for the link fields

        if cache_size == 0:

            def wrapper(*args, **kwds):
                # no caching, just do a statistics update after a successful call
                result = user_function(*args, **kwds)
                stats[MISSES] += 1
                return result

        elif cache_size is None:

            def wrapper(*args, **kwds):
                # simple caching without ordering or size limit
                key = make_key(args, kwds, typed)
                result = cache_get(key, root)  # root used here as a unique not-found sentinel
                if result is not root:
                    stats[HITS] += 1
                    return result
                result = user_function(*args, **kwds)
                cache[key] = result
                stats[MISSES] += 1
                return result

        else:

            def wrapper(*args, **kwds):
                # size limited caching that tracks accesses by recency
                key = make_key(args, kwds, typed) if kwds or typed else args
                with lock:
                    link = cache_get(key)
                    if link is not None:
                        # record recent use of the key by moving it to the front of the list
                        root, = nonlocal_root
                        link_prev, link_next, key, result = link
                        link_prev[NEXT] = link_next
                        link_next[PREV] = link_prev
                        last = root[PREV]
                        last[NEXT] = root[PREV] = link
                        link[PREV] = last
                        link[NEXT] = root
                        stats[HITS] += 1
                        return result
                result = user_function(*args, **kwds)
                with lock:
                    root, = nonlocal_root
                    if key in cache:
                        # getting here means that this same key was added to the
                        # cache while the lock was released.  since the link
                        # update is already done, we need only return the
                        # computed result and update the count of misses.
                        pass
                    elif _len(cache) >= cache_size:
                        # use the old root to store the new key and result
                        oldroot = root
                        oldroot[KEY] = key
                        oldroot[RESULT] = result
                        # empty the oldest link and make it the new root
                        root = nonlocal_root[0] = oldroot[NEXT]
                        oldkey = root[KEY]
                        oldvalue = root[RESULT]
                        root[KEY] = root[RESULT] = None
                        # now update the cache dictionary for the new links
                        del cache[oldkey]
                        cache[key] = oldroot
                    else:
                        # put result in a new link at the front of the list
                        last = root[PREV]
                        link = [last, root, key, result]
                        last[NEXT] = root[PREV] = cache[key] = link
                    stats[MISSES] += 1
                return result

        def cache_info():
            """Report cache statistics"""
            with lock:
                return _CacheInfo(stats[HITS], stats[MISSES], cache_size, len(cache))

        def cache_clear():
            """Clear the cache and cache statistics"""
            with lock:
                cache.clear()
                root = nonlocal_root[0]
                root[:] = [root, root, None, None]
                stats[:] = [0, 0]

        wrapper.__wrapped__ = user_function
        wrapper.cache_info = cache_info
        wrapper.cache_clear = cache_clear
        return update_wrapper(wrapper, user_function)

    return decorating_function
