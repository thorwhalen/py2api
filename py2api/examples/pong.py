from flask import Flask

app = Flask(__name__)


def pong(x=0, arr=None):
    if x is 0:
        return 'pong'
    else:
        if arr is None:
            return f"{x} pongs"
        else:
            import pandas as pd
            return pd.DataFrame({'vm': arr * x, 'something': len(arr) * ['boo']})


if __name__ == "__main__":
    from flask import jsonify
    from py2api.py2rest.obj_wrap import WebObjWrapper
    from py2api.py2rest.input_trans import InputTrans, _ARGNAME, _ELSE, _ARGS, _JSON
    from py2api.output_trans import OutputTrans, _ATTR
    from py2api.py2rest.app_maker import mk_app, dflt_run_app_kwargs
    import sys

    import numpy as np
    import pandas as pd

    input_trans = InputTrans({
        _ARGNAME: {
            'arr': {
                _ARGS: lambda x: x.split(','),
                _JSON: lambda x: np.array(x)
            },
            'x': int
        }
    })


    def convert_pong_outputs(out):
        if isinstance(out, pd.DataFrame):
            return jsonify(out.to_dict())
        else:
            return jsonify({'_result': out})


    output_trans = OutputTrans({
        _ATTR: {
            'pong': convert_pong_outputs
        },
        _ELSE: lambda x: jsonify({'_result': x})
    })

    wrap = WebObjWrapper(obj_constructor=sys.modules[__name__],  # wrap this current module
                         obj_constructor_arg_names=[],  # no construction, so no construction args
                         permissible_attr=['pong'],
                         input_trans=input_trans,
                         output_trans=output_trans,
                         name='/',
                         debug=0)

    app = mk_app(app_name=__name__, routes=[wrap])

    app.run(**dflt_run_app_kwargs())
