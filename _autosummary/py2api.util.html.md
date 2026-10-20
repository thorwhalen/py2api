# py2api.util

Utilities for py2api: attribute-permission filters, docstring enhancement,
and output-to-JSON conversion helpers used by the object wrappers.

### Functions

| `argname_based_specs_from`(specs)                                                            |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
|----------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `default_to_jdict`(result[, result_field])                                                   |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| [`enhanced_docstr`](#py2api.util.enhanced_docstr)(func)                       | Returns the string of func._\_doc_\_ where it prepended the function call description (i.e. function name, arguments, and default values).                                                                                                                                                                                                                                                                                                                                                                                  |
| `get_attr_recursively`(obj, attr[, default])                                                 |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| [`get_pattern_from_attr_permissions_dict`](#py2api.util.get_pattern_from_attr_permissions_dict)(...) | Construct a compiled regular expression from a permissions dict containing a list of what to include and exclude. Will be used in ObjWrapper if permissible_attr_pattern is a dict. Note that the function enforces certain patterns (like inclusions ending with $ unless they end with <br/><br/>```<br/>*<br/>```<br/><br/>, etc. What is not checked for is that the "." was meant, or if it was "." that was meant. This shouldn't be a problem in most cases, and hey! It's to the user to know regular expressions!. |
| `obj_str_from_obj`(obj)                                                                      |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |

### Classes

| `PermissibleAttr`([permissible_attrs])   |    |
|------------------------------------------|----|

### py2api.util.enhanced_docstr(func)

Returns the string of func._\_doc_\_ where it prepended the function call description
(i.e. function name, arguments, and default values).

* **Parameters:**
  **func**
* **Returns:**

```pycon
>>> def some_function(x):
...     pass
...
>>> class SomeClass(object):
...     pass
...
>>> def foo(a, b=3, c='as', d=SomeClass, dd=some_function, ddd=None, *args, **kwargs):
...     '''some documentation...'''
...     pass
>>> print(enhanced_docstr(foo))
foo(a, b=3, c="as", d=SomeClass, dd=some_function, ddd=None, *args, **kwargs)
some documentation...
```

A function with no default arguments keeps all of its positional args
(regression: `args[:-len(dflts)]` used to drop them all when `dflts` was empty):

```pycon
>>> def no_defaults(a, b, c):
...     '''some docs'''
>>> print(enhanced_docstr(no_defaults))
no_defaults(a, b, c)
some docs
```

### py2api.util.get_pattern_from_attr_permissions_dict(attr_permissions)

Construct a compiled regular expression from a permissions dict containing a list of what to include and exclude.
Will be used in ObjWrapper if permissible_attr_pattern is a dict.
Note that the function enforces certain patterns (like inclusions ending with $ unless they end with 

```
*
```

, etc.
What is not checked for is that the “.” was meant, or if it was “.” that was meant.
This shouldn’t be a problem in most cases, and hey! It’s to the user to know regular expressions!

* **Parameters:**
  **attr_permissions** – A dict of the format {‘include’: INCLUSION_LIST, ‘exclude’: EXCLUSION_LIST}.
  Both ‘include’ and ‘exclude’ are optional, and their lists can be empty.
* **Returns:**
  a re.compile object

```pycon
>>> attr_permissions = {
...     'include': ['i.want.this', 'he.wants.that'],
...     'exclude': ['i.want', 'he.wants', 'and.definitely.not.this']
... }
>>> r = get_pattern_from_attr_permissions_dict(attr_permissions)
>>> test = ['i.want.this', 'i.want.this.too', 'he.wants.that', 'he.wants.that.other.thing',
...         'i.want.ice.cream', 'he.wants.me'
...        ]
>>> for t in test:
...     print("{}: {}".format(t, bool(r.match(t))))
i.want.this: True
i.want.this.too: False
he.wants.that: True
he.wants.that.other.thing: False
i.want.ice.cream: False
he.wants.me: False
```
