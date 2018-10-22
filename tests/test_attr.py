# -*- coding: utf-8

"""Tests for the Attribute Matching."""

import re

from py2api.permissible import MatchAttr

from hypothesis import given, assume
from hypothesis.strategies import text, characters, composite

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

#identifier = text(
#    alphabet=characters(whitelist_categories="LN",
#                        min_codepoint=0x20,
#                        max_codepoint=0x7f))

@given(a1=identifier(), a2=identifier())
def test_match_attr_string(a1, a2):
    """Check creating MatchAttr from strings."""

    assume(a1 != a2)

    m = MatchAttr(a1)
    n = MatchAttr(a1)

    o = MatchAttr(a2)

    assert m(a1) == True, "Calling MatchAttr on the original attr matches"
    assert m == n, "MatchAttrs with same match are equal"
    assert m is n, "MatchAttrs with same match are same"

    assert m != o, "MatchAttrs with different matches are not equal"

@given(a1=identifier(), a2=identifier())
def test_match_attr_re(a1, a2):

    assume(a1 != a2)

    m = re.compile(a1)

    m_a = MatchAttr(m)

    assert m_a._at == m

    assert MatchAttr(m) == m
