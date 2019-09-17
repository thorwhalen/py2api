from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import InternalServerError
from platform import system as this_system


class ClientError(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


def route_wrapper(route_ow, route_name=None):
    def route_func(**route_args):
        try:
            return route_ow(request, **route_args)
        except Exception as e:
            raise  # if _handle_error didn't raise anything specific

    if route_name is None:
        route_name = route_ow.__name__
    route_func.__name__ = route_name
    return route_func


def mk_app(app_name, routes=None, app_config=None, cors=True):
    app = Flask(app_name)
    if app_config is None:
        app_config = {'JSON_AS_ASCII': False}
    for k, v in list(app_config.items()):
        app.config[k] = v
    if cors:
        if cors is True:
            cors = {}
        CORS(app, **cors)

    # this_logger = logger.init_logger(name=app_name, tags=[app_name, 'api'])

    @app.errorhandler(InternalServerError)
    def handle_internal_server_error(e):
        print(("General error: {}".format(e)))
        response = jsonify(success=False, error="InternalServerError",
                           message="Failed to perform action: {}".format(str(e)))
        response.status_code = 500
        # this_logger.exception('{} InternalServerError default catch: Exception with stack trace!'.format(app_name))
        return response

    @app.errorhandler(ClientError)
    def handle_invalid_usage(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        # this_logger.exception('{} ClientError default catch: Exception with stack trace!'.format(app_name))
        return response

    if routes:
        app = add_routes_to_app(app, routes)

    return app


def add_routes_to_app(app, routes):
    _routes = list()
    if isinstance(routes, dict):
        for route_name, route_ow in list(routes.items()):
            _routes.append(route_wrapper(route_ow, route_name=route_name))
        routes = _routes
    else:
        for route_ow in routes:
            _routes.append(route_wrapper(route_ow))
        routes = _routes

    for route_func in routes:
        app.route(route_func.__name__, methods=['GET', 'POST'])(route_func)

    return app


def dflt_run_app_kwargs():
    dflt_kwargs = dict()

    dflt_kwargs['host'] = '0.0.0.0'
    dflt_kwargs['port'] = 5000

    if this_system() == 'Linux':
        dflt_kwargs['debug'] = 0
    else:
        dflt_kwargs['debug'] = 1

    return dflt_kwargs


from py2api.py2rest.obj_wrap import WebObjWrapper
from py2api.output_trans import OutputTrans
from py2api.py2rest.input_trans import InputTrans


class Struct:
    def __init__(self, **attrs):
        self.__dict__.update(attrs)


def dispatch_funcs_to_web_app(funcs, input_trans=None, output_trans=None, name='py2api', debug=0):
    if not isinstance(funcs, (list, tuple)) or callable(funcs):
        funcs = [funcs]
    if input_trans is None:
        input_trans = InputTrans()
    elif isinstance(input_trans, dict):
        input_trans = InputTrans(input_trans)
    if output_trans is None:
        output_trans = OutputTrans(jsonify)

    s = Struct(**{func.__name__: func for func in funcs})

    wrap = WebObjWrapper(obj_constructor=s,  # wrap this current module
                         obj_constructor_arg_names=[],  # no construction, so no construction args
                         permissible_attr=[func.__name__ for func in funcs],
                         input_trans=input_trans,
                         output_trans=output_trans,
                         name='/',
                         debug=debug)

    return mk_app(app_name=name, routes=[wrap])
