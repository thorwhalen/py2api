from __future__ import division

from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import InternalServerError
from platform import system as this_system
from py2api.errors import ClientError

def route_wrapper(route_ow, route_name=None):
    def route_func(**route_args):
        return route_ow(request, **route_args)

    route_func.__name__ = route_ow.__name__ if route_name is None else route_name
    return route_func


def mk_app(app_name, routes=None, app_config=None, cors=True):
    app = Flask(app_name)

    if app_config is None:
        app_config = {'JSON_AS_ASCII': False}

    app.config.update(app_config)

    if cors:
        if cors is True:
            cors = {}
        CORS(app, **cors)

    # this_logger = logger.init_logger(name=app_name, tags=[app_name, 'api'])

    @app.errorhandler(InternalServerError)
    def handle_internal_server_error(e):
        print("General error: {}".format(e))
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
        for route_name, route_ow in routes.items():
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
    return {
        "host": "127.0.0.1",
        "port": 5000,
        "debug": 0 if this_system() == "Linux" else 1
        }
