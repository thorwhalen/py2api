from __future__ import division

import os

from oto.misc.single_wf_snip_analysis import TaggedWaveformAnalysisForWS, DFLT_SR, DFLT_TILE_SIZE_FRM, DFLT_CHK_SIZE_FRM

from py2api.constants import _ARGNAME, _ATTR
from py2api.py2rest.obj_wrap import WebObjWrapper
from py2api.py2rest.input_trans import InputTrans
from py2api.output_trans import OutputTrans
from py2api.py2rest.app_maker import mk_app, dflt_run_app_kwargs

from numpy import ndarray, array


def ensure_array(x):
    if not isinstance(x, ndarray):
        return array(x)
    else:
        return x


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


# Adding routes to app #################################################################################################

route_func_list = [slang_lite]

module_name, _ = os.path.splitext(os.path.basename(__file__))

app = mk_app(route_func_list, app_name=module_name)


if __name__ == "__main__":
    app_run_kwargs = dflt_run_app_kwargs()
    # print("Starting the app with kwargs: {}".format(app_run_kwargs))
    app.run(**app_run_kwargs)
