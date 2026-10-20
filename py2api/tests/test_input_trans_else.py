"""``_ELSE`` is a fallback: a more specific match must win over it."""

import json

from py2api.constants import _ARGNAME, _ELSE
from py2api.py2rest.input_trans import InputTrans

SPEC = {_ARGNAME: {"index": int, "source": str}, _ELSE: json.loads}


def _found(argname):
    return InputTrans(trans_spec=SPEC).search_trans_func(None, argname, "val", SPEC)


def test_a_matching_argname_beats_else():
    assert _found("source") is str
    assert _found("index") is int


def test_else_applies_when_nothing_else_matches():
    assert _found("other") is json.loads
