# py2api.output_trans

Output transformation: build callables that convert the output of wrapped
functions and methods (e.g. to JSON-serializable forms) for the API layer.

### Classes

| [`OutputTrans`](#py2api.output_trans.OutputTrans)([trans_spec])   | OutputTrans allows to flexibly define a callable object to convert the output of a function or method.   |
|------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|

### *class* py2api.output_trans.OutputTrans(trans_spec=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

OutputTrans allows to flexibly define a callable object to convert the output of a function or method.

For more information, see InputTrans
