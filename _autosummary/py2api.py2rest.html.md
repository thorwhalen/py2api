# py2api.py2rest

REST layer for py2api: wrap objects and modules behind a Flask web service.

### Modules

| [`app_maker`](py2api.py2rest.app_maker.html.md#module-py2api.py2rest.app_maker)     | Build a Flask app that serves a py2api object wrapper over HTTP.                                                                |
|------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------|
| [`constants`](py2api.py2rest.constants.html.md#module-py2api.py2rest.constants)     | Constant names used by the py2api REST layer.                                                                                   |
| [`input_trans`](py2api.py2rest.input_trans.html.md#module-py2api.py2rest.input_trans) | Input transformation for the REST layer: parse request arguments into the Python call arguments expected by the wrapped object. |
| [`obj_wrap`](py2api.py2rest.obj_wrap.html.md#module-py2api.py2rest.obj_wrap)       | Web-facing object wrapper (adds LRU caching) for the REST layer.                                                                |
| [`rest2py`](py2api.py2rest.rest2py.html.md#module-py2api.py2rest.rest2py)         | Client helpers to call a py2api REST service from Python.                                                                       |
