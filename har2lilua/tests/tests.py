# -*- coding: utf-8 -*-
"""
har2lilua Tests
"""

from __future__ import unicode_literals
from io import open
import unittest
import har2lilua

def _read_testfiles():
    with open("test.har", "r", encoding="utf-8") as fil:
        harstring = fil.read()
    with open("test.lua", "r", encoding="utf-8") as fil:
        luastring = fil.read()
    return harstring, luastring

class TestHar2lilua(unittest.TestCase):
    def test_cleanlua(self):
        clua = har2lilua._clean_lua
        self.assertEqual(clua("'Test'"), '"\\\'Test\\\'"')
        self.assertEqual(clua('"Test[]'),  '"\\"Test[]"')
        self.assertEqual(clua("Test'", brackets=True), "[[Test']]")
        self.assertEqual(clua("'Test]", brackets=True), '"\\\'Test]"')
        self.assertEqual(clua("ффф", brackets=True), '[[ффф]]')

    def test_har2lilua(self):
        harstring, luastring = _read_testfiles()
        self.assertEqual(luastring, har2lilua.convert(harstring))

if __name__ == "__main__":
    unittest.main()
