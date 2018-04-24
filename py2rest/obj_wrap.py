from __future__ import division

from py2api.lru import lru_cache
from py2api.defaults import DFLT_LRU_CACHE_SIZE
from py2api.obj_wrap import ObjWrap
from py2api.util import default_to_jdict
from py2api.constants import ATTR
from py2api.py2rest.constants import FILE_FIELD


# TODO: "file" is for backcompatibility. Change to "_file" once coordinated.

def extract_kwargs_from_web_request(request, convert_arg=None, file_var=FILE_FIELD):
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

    def extract_kwargs_from_request(self, request):
        """
        Translate the flask request object into a dict, taking first the contents of request.arg,
        converting them to a type if the name is listed in the convert_arg property, and assigning a default value
        (if specified bu convert_arg), and then updating with the contents of request.json
        :param request: the flask request object
        :return: a dict of kwargs corresponding to the union of post and get arguments
        """
        kwargs = extract_kwargs_from_web_request(request, convert_arg=self.input_trans)

        return dict(kwargs)

    @classmethod
    def with_lru_cache(cls,
                       cache_size=DFLT_LRU_CACHE_SIZE,
                       obj_constructor=None,
                       obj_constructor_arg_names=None,  # used to determine the params of the object constructors
                       input_trans=None,
                       permissible_attr=None,  # what attributes are allowed to be accessed
                       output_trans=None,
                       debug=0):
        return cls.with_decorators(
            constructor_decorator=lru_cache(maxsize=cache_size),
            obj_constructor=obj_constructor,
            obj_constructor_arg_names=obj_constructor_arg_names,
            permissible_attr=permissible_attr,
            input_trans=input_trans,
            output_trans=output_trans,
            debug=debug
        )
