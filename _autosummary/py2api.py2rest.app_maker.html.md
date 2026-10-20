# py2api.py2rest.app_maker

Build a Flask app that serves a py2api object wrapper over HTTP.

### Functions

| `add_routes_to_app`(app, routes)               |    |
|------------------------------------------------|----|
| `dflt_run_app_kwargs`()                        |    |
| `dispatch_funcs_to_web_app`(funcs[, ...])      |    |
| `mk_app`(app_name[, routes, app_config, cors]) |    |
| `route_wrapper`(route_ow[, route_name])        |    |

### Classes

| `Struct`(\*\*attrs)   |    |
|-----------------------|----|

### Exceptions

| [`ClientError`](#py2api.py2rest.app_maker.ClientError)(message[, status_code, payload])   |    |
|-------------------------------------------------------------------------------------------------|----|

### *exception* py2api.py2rest.app_maker.ClientError(message, status_code=None, payload=None)

Bases: [`Exception`](https://docs.python.org/3/builtins/exceptions.html#Exception)
