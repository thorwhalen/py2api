# py2api
Expose python objects to external clients with minimal effort.

## For the eager

py2api allows you to role out webservices (with flask) with minimal boilerplate.

To get started quickly, have a look at the examples, and play around with edits of them.

The main boilerplate here is writing code for input and output conversion. To help with this,
we provide some tools. Have a look at the output_trans.py and py2rest/input_trans.py modules, 
especially the doctest, which should give you an idea of how to work it.

A webservice module assembled with py2api looks something like this:

```
    from mystuff import SystemService
    from py2api import OutputTrans
    from py2api.py2rest import InputTransWithAttrInURL
    
    attr_list = ['ping', 'status', 'stop', 'start', 'restart']
    
    name = '/api/process/'
    process = WebObjWrapper(
        obj_constructor=SystemService,
        obj_constructor_arg_names=['name'],
        permissible_attr=attr_list,
        input_trans=InputTransWithAttrInURL(trans_spec=None, attr_from_url=name + "(\w+)"),
        output_trans=OutputTrans(trans_spec=None),
        name=name,
        debug=0
    )
    
    app = add_routes_to_app(app, routes={
            process.__name__ + attr: process for attr in attr_list
        }
    )
```

Note the two trans_spec=None used when making the input_trans and output_trans arguments of 
WebObjWrapper. There was no need to specify any special conversion there because the methods
we were wrapping here only used simple types (string, int, float, list). 

But often, when faced with more complex types, specifying how to carry out conversion in each and every situation
constitutes a big part of the boilerplate. 
We provide tools to do this through a mapping (dict) separate from the code.
This enables tools to be created to operate on this specification.
You can specify conversion verbosely, by specifying how every argument of every function should be converted. 
If you're the type, you can also do so concisely, 
by specifying contextual rules involving the object's names and types, etc. grouping conversion rules together.

Such a (more concise) conversion specification looks like this:

```python
from py2api.constants import _ATTR, _ARGNAME, _ELSE, _VALTYPE

def ensure_array(x):
    if not isinstance(x, ndarray):
        return array(x)
    return x

trans_spec = {
        _ATTR: {
            'this_attr': list,
            'other_attr': str,
            'yet_another_attr': {
                _VALTYPE: {
                    dict: lambda x: x
                },
                _ELSE: lambda x: {'result': x}
            }
        },
        _ARGNAME: {
            'sr': int,
            'ratio': float,
            'snips': list,
            'wf': ensure_array
        },
    }
}
```

See that the conversion function could be a builtin function like list, str, float, or int,
or could be a custom function, declared on the fly with a lambda, or refering to a function
declared elsewhere. 


## Motivation

Say you have some functions, classes and/or whole modules that contain some functionality 
that you'd like to expose as a webservice. 
So you grab some python libary to do that. If you make your choice right, you won't have 
to deal with the nitty gritty details of receiving and sending web requests. 
Say, you chose flask. Good choice. Known to have minimal boiler plate.
So now all you have to do make a module and do something like this...

```
from blah import a_func_you_want_to_expose
@app.route("/a_func_you_want_to_expose/", methods=['GET'])
def _a_func_you_want_to_expose():
    # A whole bunch of boiler plate to get your arguments out
    # of the web request object, which could be in the url, the json, the data...
    # oh, and then you have to convert these all to python objects, 
    # because they're all simple types like strings, numbers and lists, 
    # you'll probably want to do some validation, perhaps add a few 
    # things that weren't really a concern of the original function, 
    # like logging, caching, providing some documentation/help, 
    # and then, oh, okay, you can call that function of yours now:

    results = a_func_you_want_to_expose(...the arguments...)

    # But wait, it's not finished! You'll need to convert these results 
    # to something that a web request can handle. Say a string or a json...
```
        
That's all. Enjoyed it?

Now do that again, and again, and again, for every fooing object you want to expose.

Still enjoy it?

We didn't. So we made py2api.

With py2api, you write the same boilerplate, but you only write it once. 
In py2api you specify all the concerns of the routes you want elsewhere, a bit like 
what OpenAPI does. But further, you have tools to reduce this specification to a set 
of conventions and rules that define them. For example, if you use a variable called 
"num" a lot, and most of the time it has to be an int, except in a few cases, your 
specification has to be just that. It looks like this:


This whole py2api thing wasn't only about minimizing the time spent on a boilerplate. 

It's also because separation of concerns is good, and in the above example, 
concerns aren't as separated as they could: You have conversion, validation, logging, 
caching. 

Also, because code reuse is good, and we don't mean copy/pasting: You probably 
have many arguments and types that show up in different places, and will end up writing, 
or copy pasting, code to handle these many times. What if you made a mistake? You'll have to 
find all those copies and correct them all.

Minimizing what you have to write to get something done is good: There's less places to look 
for bugs.
 
Consistency is good.

Et cetera.
  
