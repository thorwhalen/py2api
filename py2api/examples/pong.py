"""
This example wraps a single simple function.
Simple, but cheekily type-inconsistent.
This will give us the excuse to demo how to use InputTrans and OutputTrans with a nested conditions specification.
Here we'll use condition markers such as _ARGNAME, _ELSE, _ARGS, _JSON, _SOURCE, _ATTR, and _VALTYPE!
Looking forward to it?

Launch this script and try out asking your browser what these URLs will give you:

http://0.0.0.0:5000/?attr=pong
http://0.0.0.0:5000/?attr=pong&x=10
http://0.0.0.0:5000/?attr=pong&x=10&arr=1,2,3

You can also use postman to try the webservice out with json payloads.

You can also read and run the _test_webservice function below.

Have fun
"""


def pong(x=0, arr=None):
    if x is 0:
        return 'pong'
    else:
        if arr is None:  # if x is not 0, but no arr is given, return a dict
            return {'number': x, 'thing': 'pongs'}
        else:
            import pandas as pd  # lets make it even more difficult, and return a complex object: A dataframe
            # ... Oh no! How is the webservice going to put THAT on the wire!?
            return pd.DataFrame({'vm': arr + x, 'something': len(arr) * ['boo']})


def _test_webservice(route_root='http://0.0.0.0:5000/'):
    """Test the webservice.
    Note: Of course, first launch it!"""
    import requests

    def get_json_response_for(url_suffix='', json_payload=None):
        method = 'POST' if json_payload else 'GET'
        r = requests.request(method, url=route_root + url_suffix, json=json_payload)
        try:
            return r.json()
        except:
            return r

    assert get_json_response_for('?attr=pong') == {'_result': 'pong'}
    assert get_json_response_for('?attr=pong&x=10') == {'number': 10, 'thing': 'pongs'}

    # can also put x in the json:
    assert get_json_response_for('?attr=pong', json_payload={'x': 10}) == {'number': 10, 'thing': 'pongs'}

    assert get_json_response_for('?attr=pong&x=10', json_payload={'arr': [1, 2, 3]}) == {
        'something': {'0': 'boo', '1': 'boo', '2': 'boo'},
        'vm': {'0': 11, '1': 12, '2': 13}}

    assert get_json_response_for('?attr=pong&x=10&arr=1,2,3') == {'something': {'0': 'boo', '1': 'boo', '2': 'boo'},
                                                                  'vm': {'0': 11.0, '1': 12.0, '2': 13.0}}


if __name__ == "__main__":
    import os
    from flask import jsonify
    from py2api.py2rest.obj_wrap import WebObjWrapper
    from py2api.py2rest.input_trans import InputTrans, _ARGNAME, _ELSE, _ARGS, _JSON, _SOURCE
    from py2api.output_trans import OutputTrans, _ATTR, _VALTYPE
    from py2api.py2rest.app_maker import mk_app, dflt_run_app_kwargs, dispatch_funcs_to_web_app

    import numpy as np
    import pandas as pd

    input_trans = InputTrans({
        _ARGNAME: {  # check the name of the argument to decide on how to convert it
            'arr': {  # the way we'll convert arr depends on whether it comes from the url (args) or json.
                _SOURCE: {  # the conversion function will be chosen according to where arr was (url-args or json)
                    _ARGS: lambda x: np.array(list(map(float, x.split(',')))),  # convert csv string to numerical array
                    _JSON: lambda x: np.array(x)  # convert to numpy array
                }
            },
            'x': int  # convert to int  (this will work regardless of source, since int(10) == int('10') == 10)
        }
    })

    # the output of pong is all over the place: Sometimes a string, sometimes a dict, sometimes a DataFrame.
    # So we need to condition how we convert outputs...

    # Now, we could define a function and pass it on to OutputTrans (see comment at the end of this module).
    # But know that OutputTrans json language accommodate's for type based choices:
    output_trans = OutputTrans({
        _ATTR: {
            'pong': {  # of course, if there's only one function that's being wrapped, you don't need this condition
                _VALTYPE: {  # will check the type of the output and choose the converter accordingly
                    pd.DataFrame: lambda out: jsonify(out.to_dict()),
                    dict: lambda out: jsonify(out),
                }
            }
        },
        _ELSE: lambda x: jsonify({'_result': x})  # if no condition was met yet, just use this!
    })

    app = dispatch_funcs_to_web_app([pong], input_trans, output_trans, name=os.path.basename(__file__)[0])

    app.run(**dflt_run_app_kwargs())

    # # NOTE: That output_trans thing... We could do it by defining a function that contains the conversion logic.
    # def convert_pong_outputs(out):
    #     if isinstance(out, pd.DataFrame):
    #         return jsonify(out.to_dict())
    #     elif isinstance(out, dict):
    #         return jsonify(out)
    #     else:
    #         return jsonify({'_result': out})
    #
    #
    # output_trans = OutputTrans({
    #     _ATTR: {
    #         'pong': convert_pong_outputs
    #     },
    #     _ELSE: lambda x: jsonify({'_result': x})
    # })
