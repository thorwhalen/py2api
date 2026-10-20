# py2api

py2api: declarative construction of web-service APIs from Python objects.

Wrap a Python object (class, module, or instance) behind a permission-controlled
API surface, with pluggable input/output transformations. The [`py2api.py2rest`](py2api.py2rest.html.md#module-py2api.py2rest)
subpackage adds a Flask-based REST layer on top of the core wrappers.

### Modules

| [`constants`](py2api.constants.html.md#module-py2api.constants)       | Shared constant names and sentinel values used across py2api.                                                                                        |
|------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------|
| [`defaults`](py2api.defaults.html.md#module-py2api.defaults)         | Default values used across py2api.                                                                                                                   |
| [`errors`](py2api.errors.html.md#module-py2api.errors)             | Exception types raised by py2api wrappers (client/attribute-access errors).                                                                          |
| [`obj_wrap`](py2api.obj_wrap.html.md#module-py2api.obj_wrap)         | Base module to wrap a "controller" class for a web service REST API.                                                                                 |
| [`output_trans`](py2api.output_trans.html.md#module-py2api.output_trans) | Output transformation: build callables that convert the output of wrapped functions and methods (e.g. to JSON-serializable forms) for the API layer. |
| [`py2rest`](py2api.py2rest.html.md#module-py2api.py2rest)           | REST layer for py2api: wrap objects and modules behind a Flask web service.                                                                          |
| `scrap_obj_wrap`                                                                         | Base module to wrap a "controller" class for a web service REST API.                                                                                 |
| [`util`](py2api.util.html.md#module-py2api.util)                 | Utilities for py2api: attribute-permission filters, docstring enhancement, and output-to-JSON conversion helpers used by the object wrappers.        |
