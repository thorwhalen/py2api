"""
Run this file and try it out with curl or in a browser.

Examples
    http://127.0.0.1:5003/my_ws?attr=greet
    http://127.0.0.1:5003/my_ws?attr=greet&user=me
    http://127.0.0.1:5003/my_ws?attr=greet&dflt_greeting=Goodnight
    http://127.0.0.1:5003/my_ws?attr=greet&dflt_greeting=Goodnight&user=day
    http://127.0.0.1:5003/my_ws?attr=fcalc.whoami
    http://127.0.0.1:5003/my_ws?attr=icalc.compute&_help=1
    http://127.0.0.1:5003/my_ws?attr=fcalc.compute&x=5&y=3&op=/
    http://127.0.0.1:5003/my_ws?attr=icalc.compute&x=5&y=3&op=/
    http://127.0.0.1:5003/my_ws?attr=fcalc.compute&x=5&y=3&op=-

See that for the "+" operation, you need to urlencode (as %2B):
    http://127.0.0.1:5003/my_ws?attr=fcalc.compute&x=5&y=3&op=%2B

See that
    http://127.0.0.1:5003/my_ws?attr=fcalc.whoami
will raise a ForbiddenAttribute error, since it wasn't "registered" as a permissible_attr.

"""
import os
from flask import jsonify
# from oto.misc.single_wf_snip_analysis import TaggedWaveformAnalysisForWS

from py2api.constants import _ARGNAME, _ELSE, _ATTR
from py2api.py2rest.obj_wrap import WebObjWrapper
from py2api.py2rest.input_trans import InputTrans
from py2api.output_trans import OutputTrans
from py2api.py2rest.app_maker import mk_app, dflt_run_app_kwargs

import operator


# This is the controller code (usually a separate module) ##############################################################

class FloatCalculator(object):
    """
    A float Calculator (that is, division will be as expected).
    """
    whoami = 'a float calculator'

    def compute(self, x, op, y):
        """
        A float "x op y" operation (that is, division will be as expected).
        :param x: a number
        :param op: the operation
        :param y: another number
        :return: the result of the operation
        """
        return op(x, y)


class IntCalculator(object):
    whoami = 'an int calculator'

    def compute(self, x, op, y):
        """
        An int "x op y" operation (that is, division will be as expected).
        :param x: a number
        :param op: the operation
        :param y: another number
        :return: the result of the operation
        """
        return int(op(x, y))


class Controller(object):
    def __init__(self, user='world', dflt_greeting='Hello'):
        self.user = user
        self.dflt_greeting = dflt_greeting
        self.fcalc = FloatCalculator()
        self.icalc = IntCalculator()

    def greet(self, greeting=None):
        if greeting is None:
            greeting = self.dflt_greeting
        return "{} {}!".format(greeting, self.user)

    def do_not_give_access_to_this(self):
        return "it's a secret"


# These are special functions we want to use in our wrapper ############################################################

op_map = {
    '+': operator.add,
    '-': operator.sub,
    'x': operator.mul,
    '*': operator.mul
}

int_op_map = {'/': operator.floordiv}

float_op_map = {'/': operator.truediv}


def get_float_operator_func(op):
    op_func = op_map.get(op, None) or float_op_map.get(op, None)
    if op_func is not None:
        return op_func
    else:
        raise ValueError("No such operation: {}".format(op))


def get_int_operator_func(op):
    op_func = op_map.get(op, None) or int_op_map.get(op, None)
    if op_func is not None:
        return op_func
    else:
        raise ValueError("No such operation: {}".format(op))


input_trans = InputTrans(
    trans_spec={
        _ATTR: {  # the op argument is going to be handled differently according to the calculator type (float or int)
            'fcalc.compute': {
                _ARGNAME: {
                    'op': get_float_operator_func
                }
            },
            'icalc.compute': {
                _ARGNAME: {
                    'op': get_int_operator_func
                }
            },
        },
        _ARGNAME: {  # these argument can all be floats (don't have to be handled differently)
            'x': float,
            'y': float
        }
    })

output_trans = OutputTrans(lambda x: jsonify({'_result': x}))

# wrapper ##############################################################################################################
obj_wrapper = WebObjWrapper(obj_constructor=Controller,
                           obj_constructor_arg_names=['user', 'dflt_greeting'],
                           permissible_attr=['greet', 'fcalc.compute', 'fcalc.whoami', 'icalc.compute'],
                           input_trans=input_trans,
                           output_trans=output_trans,
                           name='/my_ws',
                           debug=1)

# Adding routes to app #################################################################################################

route_func_list = [obj_wrapper]

app = mk_app(app_name=__name__, routes=route_func_list)

if __name__ == "__main__":
    app_run_kwargs = dflt_run_app_kwargs()
    app_run_kwargs['port'] = 5003
    # print("Starting the app with kwargs: {}".format(app_run_kwargs))
    app.run(**app_run_kwargs)
