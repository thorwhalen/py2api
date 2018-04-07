"""
Input trans dict specification format

The objective is to transform a flask request into a dict that contains arguments that can be understood by the
function or method the attribute points to. Therefore it does two things:
    (1) Collect argument names and values from the request object
    (2) Transform/convert/cast the argument values to values the function or method expects
    (3) Adding arguments that haven't been specified, along with default values

How to do this is totally specified by a spec_dict.

The simplest spec_dict is the empty dict, which will result in taking all the arguments and values of the request
object (i.e. the union of the request.args and request.json dict) as is.

A step up from that would be to specify what trans function to use according to the argument name. In a perfect world,
an argument name would always point to the same "thing" which would have the same type(s), no matter what
function/method is mentioning it. An even more perfect world would be one where the reverse is also true: a same
"thing" would always have the same type(s) and name.

This argname-->trans_func can be specified in a {argname: trans_func} dict. Bare in mind that you don't have to
specify everything. For example, if an arg is expected to be a string the function/method/variable, and will be
expressed as a string in the json payload of a request (it's always a string in the request.args anyway!), then
no need to convert it to something else.

It is a good practice to strive for this perfect world when coding: A perfect correspondance between name, thing, and
type. But since the intent of py2api is to separate the API concern from the actual computation code, it shouldn't
expect the coder to write code in any particular way, even if that way is better.

Therefore the argname-->trans_func won't suffice.

So in addition to the {argname: trans_func} specification, InputTrans provides the ability to condition some
{argname: trans_func} links on the attribute.

{
    "_attr":
        {
            ATTR_NAME_1:
                {
                    '_argname': {ARG_NAME_a: trans_func_1a, ...},
                    '_else': trans_func_attr_else
                },
            ATTR_NAME_2: ...
        },
    "_argname":
        {
            ARG_NAME_b: trans_func_b
            ARG_NAME_c: ...
        }
}

When a given attribute ATTR is called with argument (name) ARGNAME whose type is VALTYPE,
the decision of what trans_func to use follows the following algorithm:
    If _attr exists and ATTR is listed in _attr:
        (say it's ATTR_NAME_1)
        If ARGNAME is listed in _attr.ATTR_NAME_1._argname:
            (say it's ARG_NAME_a)
            use trans_func_1a
        elif there is an _attr.ATTR_NAME_1._else:
            use trans_func_attr_else
    (... and if we didn't find anything yet, look in _argname...)
    If _argname exists and ARGNAME is listed in _argname:
        (say it's ARG_NAME_b)
        If VALTYPE is listed in _argname.ARG_NAME_b._valtype:
            (say it's VAL_TYPE_x)
            use trans_func_bx
        elif there is an _argname.ARG_NAME_b._else:
            use trans_func_b_else
    (... and if we didn't find anything yet, look in _valtype...)
    If _valtype exists and VALTYPE is listed in _valtype:
        (say it's VALTYPE_y)
        use trans_func_y
    (... and if we didn't find anything yet, look in _else...)
    If _else exists:
        use trans_func_else
    (... and if we didn't find anything so far, don't use a trans func at all)

IMPORTANT NOTE: The top level _valtype and _else were included for consistency and completeness, but rare are the cases
that they'd actually be included in the specification, and if used, should be used with care.
An _else at the top level will result in all arguments that were not resolved by _attr, _argname, or _valtype, to be
cast to the same single type.
Similarly, a _valtype at the top level will result in all arguments that were not resolved by _attr or _argname to be
cast a type that is only conditioned by the VALTYPE of the argument.

On top of the specification choices described above, py2web InputTrans offers the possibility of conditioning on the
"source" of the (attr, arg) pair: The source could be _arg (i.e. the args was included in requests.args) or _json
(i.e. the arg was included in request.json).
It does so by allowing yet another top level key in the trans_spec: _source.
The algorithm then becomes:
    If the arg was found in request.args, look in _source._args (which contains the same trans_spec format mentioned
    above)
    Elif the arg was found in request.json, look in _source._json (which contains the same trans_spec format mentioned
    above)
    And if not found yet, proceed as usual.
"""

from __future__ import division

from py2api.py2web.constants import FILE_FIELD


class ArgNotFound(object):
    pass


ARG_NOT_FOUND = ArgNotFound()

_ARG = '_arg'
_JSON = '_json'
_ATTR = '_attr'
_ARGNAME = '_argname'
_VALTYPE = '_valtype'
_ELSE = '_else'

DFLT_TRANS = {
    _ARG: {'type': str}
}


# def extract_kwargs_from_web_request(request):
#     kwargs = dict()
#     for k in request.args.keys():
#         if k in convert_arg:
#             if 'default' in convert_arg[k]:
#                 kwargs[k] = request.args.get(k,
#                                              type=convert_arg[k].get('type', str),
#                                              default=convert_arg[k]['default'])
#             else:
#                 kwargs[k] = request.args.get(k, type=convert_arg[k].get('type', str))
#         else:
#             kwargs[k] = request.args.get(k)
#     if request.json is not None:
#         kwargs = dict(kwargs, **request.json)
#     if 'file' in request.files:
#         kwargs[FILE_FIELD] = request.files['file']
#     return kwargs

def _preprocess_trans_dict(trans_dict):
    if trans_dict is None:
        trans_dict = dict()
    assert isinstance(trans_dict, dict), "trans_dict must be a dict"
    if _ARG not in trans_dict:
        trans_dict['_arg'] = dict()
    if _JSON not in trans_dict:
        trans_dict['_json'] = dict()
    return trans_dict


class InputTrans(object):
    def __init__(self, trans_spec=None, dflt_spec=None):
        if trans_spec is None:
            trans_spec = {}
        if dflt_spec is None:
            dflt_spec = {}

    def _get_val_from_arg(self, arg, attr):
        pass

    def search_trans_func_in_valtype(self, valtype, _valtype):
        return _valtype.get(valtype, ARG_NOT_FOUND)

    def search_trans_func_in_argname(self, argname, _argname):
        trans = _argname.get(argname, ARG_NOT_FOUND)
        if trans == ARG_NOT_FOUND:
            if _VALTYPE in _argname:
                pass

    def __call__(self, attr, request):
        input_dict = dict()
        for arg in request.args.keys():
            trans = self.attr_trans.get(_ARG)


'''
    If _attr exists and ATTR is listed in _attr:
        (say it's ATTR_NAME_1)
        If ARGNAME is listed in _attr.ATTR_NAME_1._argname:
            (say it's ARG_NAME_a)
            use trans_func_1a
        elif VALTYPE is listed in _attr.ATTR_NAME_1._valtype:
            (say it's VAL_TYPE_w)
            use trans_func_1w
        elif there is an _attr.ATTR_NAME_1._else:
            use trans_func_attr_else
    (... and if we didn't find anything yet, look in _argname...)
    If _argname exists and ARGNAME is listed in _argname:
        (say it's ARG_NAME_b)
        If VALTYPE is listed in _argname.ARG_NAME_b._valtype:
            (say it's VAL_TYPE_x)
            use trans_func_bx
        elif there is an _argname.ARG_NAME_b._else:
            use trans_func_b_else
    (... and if we didn't find anything yet, look in _valtype...)
    If _valtype exists and VALTYPE is listed in _valtype:
        (say it's VALTYPE_y)
        use trans_func_y
    (... and if we didn't find anything yet, look in _else...)
    If _else exists:
        use trans_func_else
    (... and if we didn't find anything so far, don't use a trans func at all)
'''


def old_extract_kwargs_from_web_request(request, convert_arg=None, file_var=None):
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


"""
Adding to the simple (but powerful) attr and/or argname specification of how to transform input vals,
we can add the option to condition the trans function on the value type as well.

This more complex specification would look as follows:

{
    "_attr":
        {
            ATTR_NAME_1:
                {
                    '_argname': {ARG_NAME_a: trans_func_1a, ...},
                    '_valtype': {VAL_TYPE_w: trans_func_1w, ...},
                    '_else': trans_func_attr_else
                },
            ATTR_NAME_2: ...
        },
    "_argname":
        {
            ARG_NAME_b:
                {
                    '_valtype': {VAL_TYPE_x: trans_func_bx, ...}
                    '_else': trans_func_b_else
                },
            ARG_NAME_c: ...
        }
    "_valtype":
        {
            VALTYPE_y: trans_func_y,
            VALTYPE_z: ...,
        }
    '_else": trans_func_else
}

When a given attribute ATTR is called with argument (name) ARGNAME whose type is VALTYPE,
the decision of what trans_func to use follows the following algorithm:
    If _attr exists and ATTR is listed in _attr:
        (say it's ATTR_NAME_1)
        If ARGNAME is listed in _attr.ATTR_NAME_1._argname:
            (say it's ARG_NAME_a)
            use trans_func_1a
        elif VALTYPE is listed in _attr.ATTR_NAME_1._valtype:
            (say it's VAL_TYPE_w)
            use trans_func_1w
        elif there is an _attr.ATTR_NAME_1._else:
            use trans_func_attr_else
    (... and if we didn't find anything yet, look in _argname...)
    If _argname exists and ARGNAME is listed in _argname:
        (say it's ARG_NAME_b)
        If VALTYPE is listed in _argname.ARG_NAME_b._valtype:
            (say it's VAL_TYPE_x)
            use trans_func_bx
        elif there is an _argname.ARG_NAME_b._else:
            use trans_func_b_else
    (... and if we didn't find anything yet, look in _valtype...)
    If _valtype exists and VALTYPE is listed in _valtype:
        (say it's VALTYPE_y)
        use trans_func_y
    (... and if we didn't find anything yet, look in _else...)
    If _else exists:
        use trans_func_else
    (... and if we didn't find anything so far, don't use a trans func at all)

IMPORTANT NOTE: The top level _valtype and _else were included for consistency and completeness, but rare are the cases
that they'd actually be included in the specification, and if used, should be used with care.
An _else at the top level will result in all arguments that were not resolved by _attr, _argname, or _valtype, to be
cast to the same single type.
Similarly, a _valtype at the top level will result in all arguments that were not resolved by _attr or _argname to be
cast a type that is only conditioned by the VALTYPE of the argument.

On top of the specification choices described above, py2web InputTrans offers the possibility of conditioning on the
"source" of the (attr, arg) pair: The source could be _arg (i.e. the args was included in requests.args) or _json
(i.e. the arg was included in request.json).
It does so by allowing yet another top level key in the trans_spec: _source.
The algorithm then becomes:
    If the arg was found in request.args, look in _source._args (which contains the same trans_spec format mentioned
    above)
    Elif the arg was found in request.json, look in _source._json (which contains the same trans_spec format mentioned
    above)
    And if not found yet, proceed as usual.
"""