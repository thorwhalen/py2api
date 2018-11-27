

from .constants import TRANS_NOT_FOUND, _OUTPUT_TRANS, _ATTR, _VALTYPE, _ELSE


class OutputTrans(object):
    """

    """

    def __init__(self, trans_spec=None):
        """
        An output transformer builder.
        >>> from py2api.output_trans import OutputTrans
        >>> from py2api.constants import _ATTR, _VALTYPE, _ELSE, _OUTPUT_TRANS
        >>>
        >>> trans_spec = {
        ...     _OUTPUT_TRANS : {
        ...         'csv': lambda x: ",".join(map(str, x))
        ...     },
        ...     _ATTR: {
        ...         'this_attr': list,
        ...         'other_attr': str,
        ...         'yet_another_attr': {
        ...             _VALTYPE: {
        ...                 dict: lambda x: x
        ...             },
        ...             _ELSE: lambda x: {'result': x}
        ...         }
        ...     },
        ... }
        >>> output_trans = OutputTrans(trans_spec)
        >>>
        >>> output_trans([1,4,2,5], output_trans='csv')
        '1,4,2,5'
        >>> output_trans(tuple(['was', 'a', 'tuple']), attr='this_attr')
        ['was', 'a', 'tuple']
        >>> output_trans(tuple(['was', 'a', 'tuple']), attr='other_attr')
        "('was', 'a', 'tuple')"
        >>> output_trans({'a': 'dict'}, attr='yet_another_attr')
        {'a': 'dict'}
        >>> output_trans(['not', 'a', 'dict'], attr='yet_another_attr')
        {'result': ['not', 'a', 'dict']}
        >>>
        >>> # An example of type-based conversion, using pandas and numpy if present
        >>> try:
        ...     import pandas as pd
        ...     import numpy as np
        ...     trans_spec = {
        ...         _VALTYPE : {
        ...             pd.DataFrame: lambda x: {'result': x.to_dict(orient='records')},
        ...             np.ndarray: lambda x: {'result': x.tolist()}
        ...         }
        ...     }
        ...     output_trans = OutputTrans(trans_spec)
        ...     df = pd.DataFrame({'A': [1,2,3, 4], 'B': ['a', 'ab', 'abc', 'abcd']})
        ...     print(output_trans(df))
        ...     arr = np.array([[2,3,4], [1,2,3]])
        ...     print(output_trans(arr))
        ... except ImportError:
        ...     pass
        ...
        {'result': [{'A': 1, 'B': 'a'}, {'A': 2, 'B': 'ab'}, {'A': 3, 'B': 'abc'}, {'A': 4, 'B': 'abcd'}]}
        {'result': [[2, 3, 4], [1, 2, 3]]}
        """
        if trans_spec is None:
            trans_spec = {}
        elif callable(trans_spec):
            trans_spec = {_ELSE: trans_spec}
        self.trans_spec = trans_spec

    def search_trans_func(self, attr, val, trans_spec, output_trans=None):
        trans_func = TRANS_NOT_FOUND  # fallback default (i.e. "found nothing")
        if callable(trans_spec):
            return trans_spec
        elif isinstance(trans_spec, dict):
            if len(trans_spec) == 0:
                return TRANS_NOT_FOUND
            elif len(trans_spec) > 0:
                ############### search _OUTPUT_TRANS #######
                if output_trans is not None:
                    _trans_spec = trans_spec.get(_OUTPUT_TRANS, {}).get(output_trans, {})
                    if _trans_spec:
                        trans_func = self.search_trans_func(
                            attr, val, trans_spec=_trans_spec, output_trans=output_trans)

                        if trans_func is not TRANS_NOT_FOUND:
                            return trans_func

                ############### search _ATTR ###############
                _trans_spec = trans_spec.get(_ATTR, {}).get(attr, {})
                if _trans_spec:
                    trans_func = self.search_trans_func(attr, val, trans_spec=_trans_spec)

                if trans_func is not TRANS_NOT_FOUND:
                    return trans_func

                ############### search _VALTYPE #############
                if _VALTYPE in trans_spec:
                    for _type, _type_trans_spec in list(trans_spec[_VALTYPE].items()):
                        if isinstance(val, _type):
                            return _type_trans_spec

                ############### _ELSE #######################
                if _ELSE in trans_spec:
                    return self.search_trans_func(attr, val, trans_spec[_ELSE])
                else:
                    return TRANS_NOT_FOUND

    def __call__(self, val, attr=None, output_trans=None):
        trans_func = self.search_trans_func(attr, val, trans_spec=self.trans_spec, output_trans=output_trans)
        if trans_func is not TRANS_NOT_FOUND:  # if there is...
            trans_val = trans_func(val)  # ... convert the val
        else:  # if there's not...
            trans_val = val  # ... just take the val as is
        return trans_val
