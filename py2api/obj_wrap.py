"""
Base module to wrap a "controller" class for a web service REST API.

This module is stripped to it's minimal (but still powerful) functionality, containing only two imports from the
Python's (2.7) standard library: re and json, and includes all necessary code in this single .py file.

Many useful utils to extend it's functionality are included elsewhere so as to enable the deployment of
minimum-necessary code, crucial, for instance, for micro-services.
"""

from py2api.errors import MissingAttribute, ForbiddenAttribute
from py2api.util import PermissibleAttr, default_to_jdict, get_attr_recursively, enhanced_docstr
from py2api.constants import _OUTPUT_TRANS, _HELP

########################################################################################################################
# Dev Notes
"""
(1) Might want to change all "reserved" strings (such as attr (see ATTR), result (see DFLT_RESULT_FIELD),
and file (see py2rest constant FILE_FIELD) to be prefixed by an underscore,
so as to have extra protection against collision.
"""


########################################################################################################################


class ObjWrap(object):
    def __init__(self,
                 obj_constructor=None,
                 obj_constructor_arg_names=None,  # used to determine the params of the object constructors
                 permissible_attr=None,
                 input_trans=None,  # input processing: Callable specifying how to prepare arguments for methods
                 output_trans=None,  # output processing: Function to convert output
                 name=None,
                 debug=0):
        """
        An class that constructs a wrapper around an object.
        An object could be a function, module, or instantiated class object (the usual case).

        Use case: Expose functionality (usually a "controller") to a web service API or script, without most of the
        boilerplate code to process input and output.

        It takes care of allowing access only to specific attributes (i.e. module variable or functions, or object
        methods).

        It also takes care of LRU caching objects constructed before (so they don't need to be re-constructed for every
        API call), and converting request.json and request.args arguments to the types that will be recognized by
        the method calls.

        :param obj_constructor: a function that, given some arguments, constructs an object. It is this object
            that will be wrapped for the webservice
        :param obj_constructor_arg_names:
        :param permissible_attr: a boolean function that specifies whether an attr is allowed to be accessed
            Usually constructed using PermissibleAttr class.
        :param input_trans: None (default) or a callable that takes a request object, and returns
            a (attr, kwargs) pair, where kwargs is a {argname: val, ...} input_data.
            That is, it takes care both of extracting the attr and the (argname, val) pairs from
            request and converting the raw val (i.e. in the format given by request (often a string)) into the python
            type that the underlying function (obj specified by attr) expects.
            Note the input_trans is usually constructed with a function factory class that uses it's parameters to
            adapt to each attr, similarly as with input_trans and output_trans.
        :param output_trans: (input processing) Function to convert an output before returning it to the outside world.
            Note the input_trans is usually constructed with a function factory class that uses it's parameters to
            adapt to each attr, similarly as with input_trans and output_trans.
        :param cache_size: The size (and int) of the LRU cache. If equal to 1 or None, the constructed object will not
            be LRU-cached.
        """
        if not callable(obj_constructor):
            # not isinstance(obj_constructor, type): (but that doesn't work because type is wrapped in lru sometimes
            self.obj_constructor = lambda: obj_constructor  # it's the object itself
        else:
            self.obj_constructor = obj_constructor

        if obj_constructor_arg_names is None:  # no constructor arguments
            obj_constructor_arg_names = []
        elif isinstance(obj_constructor_arg_names, str):  # a single constructor argument
            obj_constructor_arg_names = [obj_constructor_arg_names]
        self.obj_constructor_arg_names = obj_constructor_arg_names

        if not callable(permissible_attr):
            permissible_attr = PermissibleAttr(permissible_attrs=permissible_attr)
        self.permissible_attr = permissible_attr
        if permissible_attr is None:
            raise ValueError("Need to permit SOME attributes for an ObjWrap to work")

        assert callable(input_trans), "input_trans needs to be a callable"
        self.input_trans = input_trans  # a specification of how to convert specific argument names or types

        # self.obj_wrap = obj_wrap
        if output_trans is None:
            def _output_trans(result, *args, **kwargs):
                return result
            self.output_trans = _output_trans
        else:
            assert callable(output_trans), "input_trans needs to be a callable"
            self.output_trans = output_trans

        self.debug = debug
        if name is not None:
            self.__name__ = name

    def obj_attr(self, obj_spec, attr):
        """
        Method takes care of:
            Constructing a root object (or returning it from the LRU cache if it's already there)
            Giving access to an attribute of that root object.
        Does not take care of allowing or disallowing access to an attribute: robj takes care of that.
        :param obj_spec: specification of the base object
        :param attr: The attribute we want to access
        :return:
        """

        # get or make the base object
        if isinstance(obj_spec, dict):
            obj_spec = self.obj_constructor(**obj_spec)
            print(obj_spec, attr)
        elif isinstance(obj_spec, (tuple, list)):
            obj_spec = self.obj_constructor(*obj_spec)
        elif obj_spec is not None:
            obj_spec = self.obj_constructor(obj_spec)
        else:
            obj_spec = self.obj_constructor()

        # at this point obj is an actual obj_constructor constructed object...
        # ... so get the leaf (attr) object
        return get_attr_recursively(obj_spec, attr)  # get the (possibly nested) attribute object

    def __call__(self, request, **route_args):
        """
        Translates a request to an object access (get property value or call object method).
            Uses self.get_kwargs_from_request(request) to get a dict of kwargs from request.arg
        and request.json.
            The object to be constructed (or retrieved from cache) is determined by the self.obj_constructor_arg_names
        list. The names listed there will be extracted from the request kwargs and passed on to the object constructor
        (or cache).
            The attribute (property or method) to be accessed is determined by the 'attr' argument, which is a
        period-separated string specifying the path to the attribute (e.g. "this.is.what.i.want" will access
        obj.this.is.what.i.want).
            A requested attribute is first checked against "self._is_permissible_attr" before going further.
        The latter method is used to control access to object attributes.
        :param request: A flask request or args (for scripts)
        :return: The value of an object's property, or the output of a method.
        """

        ###### Extract the needed data from request and format values ##################################################
        # get an input_data from the request, and format it's values (might depend on attr, so passed along)
        attr, input_data = self.input_trans(request, **route_args)

        if self.debug:
            print(("attr={}, input_data = {}".format(attr, input_data)))

        # make sure attr is there, and is permissible
        if attr is None:
            raise MissingAttribute()
        elif not self.permissible_attr(attr):
            raise ForbiddenAttribute(attr)

        ###### Get or construct the attribute object being accessed ####################################################
        # pop off any arguments that are meant to be for the base obj (module, function, class instance) constructor
        obj_kwargs = {k: input_data.pop(k) for k in self.obj_constructor_arg_names if k in input_data}

        if self.debug:
            print(("attr={}, obj_kwargs = {}, input_data = {}".format(attr, obj_kwargs, input_data)))

        # make the attribute object
        obj_attr = self.obj_attr(obj_spec=obj_kwargs, attr=attr)

        ###### Handle some special args ################################################################################
        _help = input_data.pop(_HELP, None)
        if _help:
            return enhanced_docstr(obj_attr)

        ###### Return attribute, or call it with input_data kwargs, and transform output ###############################
        # Pop off the special output_trans argument, if there
        # NOTE: Could also implement something allowing to pass arguments to output_trans_func/
        # NOTE: Decided to avoid being even less YAGNI than I already am!
        output_trans = input_data.pop(_OUTPUT_TRANS, None)

        # call a method or get property
        if callable(obj_attr):  # the user wants to call obj on the input_data arguments
            result = obj_attr(**input_data)
        else:  # the obj is itself the what the user wants
            result = obj_attr

        return self.output_trans(result, attr, output_trans=output_trans)

    @classmethod
    def with_decorators(cls,
                        constructor_decorator=None,
                        # obj_attr_decorator=None,
                        obj_constructor=None,
                        obj_constructor_arg_names=None,
                        permissible_attr=None,
                        input_trans=None,
                        output_trans=default_to_jdict,
                        name=None,
                        debug=0):
        if constructor_decorator is not None:
            wrapped_obj_constructor = constructor_decorator(obj_constructor)
        else:
            wrapped_obj_constructor = obj_constructor

        # if self.obj_wrap is not None:  # might need to wrap that obj_attr?
        #     _obj_attr = self.obj_wrap(_obj_attr, attr)  # wrap it (if obj_wrap says to)

        return cls(obj_constructor=wrapped_obj_constructor,
                   obj_constructor_arg_names=obj_constructor_arg_names,
                   permissible_attr=permissible_attr,
                   input_trans=input_trans,
                   output_trans=output_trans,
                   name=name,
                   debug=debug)


        # :param: obj_wrap: None (default), or a decorator; a callable that takes the (obj, attr, input_data) triple and
        #     returns the actual (obj, input_data) that needs to be used. This is usually used when we need to modify
        #     the way the obj function works (for example, wrapping the function in a gevent process so we can call it
        #     without waiting for the response. The reason for including attr is that we (often) want to only wrap
        #     specific functions. The reason to include input_data (often ignored) is in case we want to parametrize
        #     how the function is wrapped according to some arguments that were included in request (often in the form
        #     of special argument (by convention, prefixed by an underscore) that is not an argument of the target
        #     function (and therefore should by popped out by the obj_wrap), but is there to specify how to do things
        #     differently.
        #     Note that obj_wrap is usually constructed with a function factory class that uses it's parameters to
        #     adapt to each attr, similarly as with input_trans and output_trans.
        #

        # class ObjWrapWithWrappedConstructor(ObjWrap):
        #     def __init__(self,
        #                  constructor_wrap,
        #                  obj_constructor,
        #                  obj_constructor_arg_names=None,  # used to determine the params of the object constructors
        #                  permissible_attr=None,
        #                  input_trans=None,  # input processing: Callable specifying how to prepare ws arguments for methods
        #                  obj_wrap=None,
        #                  output_trans=default_to_jdict,  # output processing: Function to convert an output to a jsonizable dict
        #                  debug=0):
        #         super(ObjWrapWithWrappedConstructor, self).__init__(obj_constructor,
        #                                                             obj_constructor_arg_names=obj_constructor_arg_names,
        #                                                             permissible_attr=permissible_attr,
        #                                                             input_trans=input_trans,
        #                                                             obj_wrap=obj_wrap,
        #                                                             output_trans=output_trans,
        #                                                             debug=debug)
        #         self.obj_constructor = constructor_wrap(obj_constructor)

        # obj_constructor,
        # obj_constructor_arg_names = None,  # used to determine the params of the object constructors
        # permissible_attr = None,
        # input_trans = None,  # input processing: Callable specifying how to prepare ws arguments for methods
        # obj_wrap = None,
        # output_trans = default_to_jdict,  # output processing: Function to convert an output to a jsonizable dict
        # debug = 0):

        # class ObjWrap(object):
        #     def __init__(self,
        #                  obj_constructor,
        #                  obj_constructor_arg_names=None,  # used to determine the params of the object constructors
        #                  permissible_attr=None,
        #                  input_trans=None,  # input processing: Callable specifying how to prepare ws arguments for methods
        #                  obj_wrap=None,
        #                  output_trans=default_to_jdict,  # output processing: Function to convert an output to a jsonizable dict
        #                  cache_size=DFLT_LRU_CACHE_SIZE,
        #                  debug=0):
        #
        #         if isinstance(cache_size, int) and cache_size != 1:
        #             self.obj_constructor = lru_cache(cache_size=cache_size)(obj_constructor)
        #         elif cache_size is None or cache_size == 1:
        #             self.obj_constructor = obj_constructor
        #         else:
        #             raise ValueError("cache_size must be an int or None")
