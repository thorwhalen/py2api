"""
Say you have a module (say, operator) and you want to expose everything in it to a webservice.
This shows you how you can do this in a few lines.

WARNING: DO THIS AT HOME (but never on an actual prod server).
--> Reason is, since you're giving access to EVERYTHING, there's ways to use the power of python to backtrack into
the actual system and make damage.

The usual way to wrap a module, function, or object and expose to a webservice is to define an explicit list of
attributes that can be access, which ensures that nothing else can. It's possible to use regular expressions to get more
be more expressive, but if you do so, be careful not to expose something you don't want to! A good practice there is
to not allow anything starting with a "_" or ending with a "*" (which will give access to everything under an attribute

Run the web service and try things like:
    http://0.0.0.0:5000/os?attr=path.isdir&s=/
    http://0.0.0.0:5000/os?attr=path.isfile&path=not_existing_file.txt
etc.

"""
from __future__ import division

import os

from flask import jsonify
from py2api.py2rest.obj_wrap import WebObjWrapper
from py2api.py2rest.input_trans import InputTrans
from py2api.output_trans import OutputTrans
from py2api.py2rest.app_maker import mk_app, dflt_run_app_kwargs


os_path_wrap = WebObjWrapper(obj_constructor=os,  # if not a callable, the wrapper wraps always the same object
                             obj_constructor_arg_names=[],  # no construction, so no construction args
                             permissible_attr='path\..*',  # allows all attributes below path.
                             input_trans=InputTrans.from_argname_trans_dict({}),  # standard input_trans
                             output_trans=OutputTrans(trans_spec=lambda x: jsonify({'_result': x})),
                             name='/os',
                             debug=0)

app = mk_app(app_name='example', routes=[os_path_wrap])

if __name__ == "__main__":
    app.run(**dflt_run_app_kwargs())
