from __future__ import division

from py2api.lru import lru_cache
from py2api.defaults import DFLT_LRU_CACHE_SIZE
from py2api.obj_wrap import ObjWrap
from py2api.util import default_to_jdict
from py2api.constants import ATTR
from py2api.py2rest.constants import FILE_FIELD


# TODO: "file" is for backcompatibility. Change to "_file" once coordinated.

class WebObjWrapper(ObjWrap):
    @classmethod
    def with_lru_cache(cls,
                       cache_size=DFLT_LRU_CACHE_SIZE,
                       obj_constructor=None,
                       obj_constructor_arg_names=None,  # used to determine the params of the object constructors
                       input_trans=None,
                       permissible_attr=None,  # what attributes are allowed to be accessed
                       output_trans=None,
                       name=None,
                       debug=0):
        return cls.with_decorators(
            constructor_decorator=lru_cache(cache_size=cache_size),
            obj_constructor=obj_constructor,
            obj_constructor_arg_names=obj_constructor_arg_names,
            permissible_attr=permissible_attr,
            input_trans=input_trans,
            output_trans=output_trans,
            name=name,
            debug=debug
        )
