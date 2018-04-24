from __future__ import division

import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from platform import system as this_system
from werkzeug.exceptions import InternalServerError
from oto.ws.ws_errors import ClientError
from oto.pj.stag.util.logging_utils import logger

from oto.misc.single_wf_snip_analysis import TaggedWaveformAnalysisForWS, DFLT_SR, DFLT_TILE_SIZE_FRM, DFLT_CHK_SIZE_FRM

from py2api.constants import _ARGNAME, _ATTR
from py2api.py2rest.obj_wrap import WebObjWrapper
from py2api.py2rest.input_trans import InputTrans
from py2api.output_trans import OutputTrans

from numpy import ndarray, array


def ensure_array(x):
    if not isinstance(x, ndarray):
        return array(x)
    else:
        return x


if this_system() == 'Linux':
    DEBUG_MODE = 0
    PORT = 5003
else:
    DEBUG_MODE = 1
    PORT = 5003

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
CORS(app)

module_name, _ = os.path.splitext(os.path.basename(__file__))

this_logger = logger.init_logger(name=module_name, tags=[module_name, 'api'])


@app.errorhandler(InternalServerError)
def handle_internal_server_error(e):
    print("General error: {}".format(e))
    response = jsonify(success=False, error="InternalServerError",
                       message="Failed to perform action: {}".format(str(e)))
    response.status_code = 500
    this_logger.exception('{} InternalServerError default catch: Exception with stack trace!'.format(module_name))
    return response


@app.errorhandler(ClientError)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    this_logger.exception('idacc_ws ClientError default catch: Exception with stack trace!')
    return response


# permissions ##########################################################################################################
slang_inclusion_list = [
    'fit',
]

attr_permissions = {'include': slang_inclusion_list, 'exclude': []}

input_trans = InputTrans(
    trans_spec={
        _ARGNAME: {
            'sr': int,
            'tile_size_frm': int,
            'chk_size_frm': int,
            'n_snips': int,
            'wf': ensure_array
        }
    })

output_trans = OutputTrans(lambda x: {'_result': x})


# constructor ##########################################################################################################
def slang_constructor(sr=DFLT_SR, tile_size_frm=DFLT_TILE_SIZE_FRM, chk_size_frm=DFLT_CHK_SIZE_FRM):
    return TaggedWaveformAnalysisForWS(sr=sr, tile_size_frm=tile_size_frm, chk_size_frm=chk_size_frm)


# wrapper ##############################################################################################################
slang_lite = WebObjWrapper(obj_constructor=slang_constructor,
                           obj_constructor_arg_names=['sr', 'tile_size_frm', 'chk_size_frm'],
                           permissible_attr=attr_permissions,
                           input_trans=input_trans,
                           output_trans=output_trans,
                           name='slang_lite',
                           debug=0)


def route_wrapper(route_ow, route_name=None):
    def route_func():
        try:
            return jsonify(route_ow(request))
        except Exception as e:
            raise  # if _handle_error didn't raise anything specific
    if route_name is None:
        route_name = route_ow.__name__
    route_func.__name__ = route_name
    return route_func

# # API route ############################################################################################################
# def slang_lite():
#     try:
#         return jsonify(slang_lite_ow(request))
#     except Exception as e:
#         raise  # if _handle_error didn't raise anything specific
#


# Adding routes to app #################################################################################################

# route_func_list = [slang_lite]

route_func_list = [
    route_wrapper(slang_lite)
]

for route_func in route_func_list:
    app.route("/" + route_func.__name__ + "/", methods=['GET', 'POST'])(route_func)

if __name__ == "__main__":
    # print("Starting the app with host {} on port {} with debug={}...".format(host, app_port, debug))
    app.run(host='0.0.0.0', port=PORT, debug=DEBUG_MODE)
