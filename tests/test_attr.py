# -*- coding: utf-8

"""Tests for the Attribute Matching."""

import re

from py2api.permissible import (
    MatchAttr,
    AttributeFilter,
    PermissionDeniedError)

from hypothesis import given, assume
from hypothesis.strategies import text, characters, composite, lists
from pytest import raises

@composite
def identifier(draw):
    c = draw(text(alphabet=characters(whitelist_categories="L",
                                      min_codepoint=0x20,
                                      max_codepoint=0x7f),
                  min_size=1))
    cs = draw(text(alphabet=characters(whitelist_categories="LN",
                                       min_codepoint=0x20,
                                       max_codepoint=0x7f)))
    return c + cs

@given(a1=identifier(), a2=identifier())
def test_match_attr_string(a1, a2):
    """Check creating MatchAttr from strings."""

    assume(a1 != a2)

    f1 = "^%s$" % a1
    f2 = "^%s$" % a2

    m = MatchAttr(f1)
    n = MatchAttr(f1)

    o = MatchAttr(f2)

    assert m(a1) == True, "Calling MatchAttr on the original attr matches"
    assert m == f1, "MatchAttr == its string "
    assert m == n, "MatchAttrs with same match are equal"
    assert m is n, "MatchAttrs with same match are same"

    assert m != o, "MatchAttrs with different matches are not equal"

@given(a1=identifier(), a2=identifier())
def test_match_attr_re(a1, a2):
    """Check creating MatchAttr from a regular expression."""
    assume(a1 != a2)

    f1 = "^%s$" % a1
    f2 = "^%s$" % a2

    m = re.compile(f1)

    m_a = MatchAttr(m)

    assert m_a._at == m, "MatchAttr._at == its re"
    assert MatchAttr(m) == m, "MatchAttr == its re"

@given(i_p=identifier(), i_d=identifier())
def test_permit_deny_attr(i_p, i_d):
    """Check permitting and denying attributes with composite policies"""

    assume(i_p != i_d)

    p = MatchAttr("^%s$" % i_p)
    d = MatchAttr("^%s$" % i_d)

    def pol(attr):
        return p(attr) and not d(attr)

    assert pol(i_p), "Composite policy permits"
    assert not pol(i_d), "Composite policy denies"

@given(attrs=lists(identifier(), min_size=1))
def test_default_deny(attrs):
    """Check that the default attribute policy is deny_all"""

    pol = AttributeFilter()

    class A(object):
        def __getattr__(self, attr):
            return "hello"

    obj = A()

    @pol
    def f(a, attr):
        return getattr(a, attr)

    for attr in attrs:
        with raises(PermissionDeniedError):
            assert not f(obj, attr) == "hello"

@given(allows=lists(identifier(), min_size=1),
       denies=lists(identifier(), min_size=1))
def test_allows_denies(allows, denies):
    assume(all(a not in denies for a in allows) and all(d not in allows for d in denies))

    flt = AttributeFilter(allow=("^%s$" % a for a in allows),
                          deny=("^%s$" % d for d in denies))

    assert(all("^%s$" % a in flt._a for a in allows))
    assert(all("^%s$" % a in flt._d for a in denies))

    class A(object):
        def __getattr__(self, attr):
            return "Hello"

    obj = A()

    @flt
    def f(a, attr):
        return getattr(a, attr)

    assert(all(f(obj, allow) == "Hello" for allow in allows))

    for attr in denies:
        with raises(PermissionDeniedError):
            assert f(obj, attr) != "Hello"
