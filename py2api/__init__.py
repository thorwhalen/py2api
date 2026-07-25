"""py2api: declarative construction of web-service APIs from Python objects.

Wrap a Python object (class, module, or instance) behind a permission-controlled
API surface, with pluggable input/output transformations. The :mod:`py2api.py2rest`
subpackage adds a Flask-based REST layer on top of the core wrappers.
"""

from .obj_wrap import ObjWrap
from .output_trans import OutputTrans
