from __future__ import division

from py2api.defaults import DFLT_LRU_CACHE_SIZE
from py2api.obj_wrap import ObjWrap
from py2api.util import default_to_jdict

# TODO: "file" is for backcompatibility. Change to "_file" once coordinated.
DFLT_FILE_VAR = 'file'


def extract_kwargs_from_web_request(request, convert_arg=None, file_var=DFLT_FILE_VAR):
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


class WebObjWrapper(ObjWrap):
    def __init__(self,
                 obj_constructor,
                 obj_constructor_arg_names=None,  # used to determine the params of the object constructors
                 input_trans=None,  # input processing: Callable specifying how to prepare ws arguments for methods
                 file_var=DFLT_FILE_VAR,  # input processing: name of the variable to use if there's a 'file' in request.files
                 permissible_attr=None,  # what attributes are allowed to be accessed
                 output_trans=default_to_jdict,  # output processing: Function to convert an output to a jsonizable dict
                 cache_size=DFLT_LRU_CACHE_SIZE,
                 debug=0):
        """
        :param obj_constructor: a function that, given some arguments, constructs an object. It is this object
            that will be wrapped for the webservice
        :param obj_constructor_arg_names:
        :param input_trans: (processing) a dict keyed by variable names (str) and valued by a dict containing a
            'type': a function (typically int, float, bool, and list) that will convert the value of the variable
                to make it web service compliant
            'default': A value to assign to the variable if it's missing.
        :param file_var: name of the variable to use if there's a 'file' in request.files
        :param permissible_attr: a boolean function that specifies whether an attr is allowed to be accessed
            Usually constructed using PermissibleAttr class.
        :param output_trans: (input processing) Function to convert an output to a jsonizable dict
        :param cache_size: The size (and int) of the LRU cache. If equal to 1 or None, the constructed object will not
            be LRU-cached.
        :param output_trans:
        :param cache_size:
        :param debug:
        """
        super(WebObjWrapper, self).__init__(
            obj_constructor,
            obj_constructor_arg_names=obj_constructor_arg_names,
            input_trans=input_trans,
            permissible_attr=permissible_attr,
            output_trans=output_trans,
            cache_size=cache_size,
            debug=debug)
        self.file_var = file_var

    def get_kwargs_from_request(self, request):
        """
        Translate the flask request object into a dict, taking first the contents of request.arg,
        converting them to a type if the name is listed in the convert_arg property, and assigning a default value
        (if specified bu convert_arg), and then updating with the contents of request.json
        :param request: the flask request object
        :return: a dict of kwargs corresponding to the union of post and get arguments
        """
        kwargs = extract_kwargs_from_web_request(request, convert_arg=self.input_trans, file_var=self.file_var)

        return dict(kwargs)
