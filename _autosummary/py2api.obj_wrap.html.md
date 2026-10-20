# py2api.obj_wrap

Base module to wrap a “controller” class for a web service REST API.

This module is stripped to it’s minimal (but still powerful) functionality, containing only two imports from the
Python’s (2.7) standard library: re and json, and includes all necessary code in this single .py file.

Many useful utils to extend it’s functionality are included elsewhere so as to enable the deployment of
minimum-necessary code, crucial, for instance, for micro-services.

### Classes

| `ObjWrap`([obj_constructor, ...])   |    |
|-------------------------------------|----|
