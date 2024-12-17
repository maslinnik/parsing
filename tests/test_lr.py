import unittest
from src import Grammar, LR
import itertools


class TestLR(unittest.TestCase):
    def test_basic(self):
        g = Grammar(['S'], ['a', 'b'], 'S')
        g.add_rule('S', 'aSb')
        g.add_rule('S', '')
        p = LR(g)
        self.assertTrue(p.predict(""))
        self.assertTrue(p.predict("ab"))
        self.assertTrue(p.predict("aabb"))
        self.assertTrue(p.predict("aaaaaabbbbbb"))
        self.assertFalse(p.predict("a"))
        self.assertFalse(p.predict("b"))
        self.assertFalse(p.predict("abb"))
        self.assertFalse(p.predict("aaabbbb"))

    def test_basic_aho(self):
        g = Grammar(list("SX"), list("ab"), 'S')
        g.add_rule('S', 'XX')
        g.add_rule('X', 'aX')
        g.add_rule('X', 'b')
        p = LR(g)

        for length in range(10):
            for s in map(lambda p: ''.join(p), itertools.product(['a', 'b'], repeat=length)):
                if s.count('b') == 2 and s[-1] == 'b':
                    assert p.predict(s)
                else:
                    assert not p.predict(s)

    def test_math(self):
        g = Grammar(list('SMT'), list('0123456789+*'), 'S')
        g.add_rule('S', 'S+M')
        g.add_rule('S', 'M')
        g.add_rule('M', 'M*T')
        g.add_rule('M', 'T')
        for digit in list('0123456789'):
            g.add_rule('T', digit)
        p = LR(g)
        self.assertTrue(p.predict("1"))
        self.assertTrue(p.predict("1*4"))
        self.assertTrue(p.predict("4+5*0"))
        self.assertTrue(p.predict("1+4+7*0"))
        self.assertFalse(p.predict(""))
        self.assertFalse(p.predict("1**1"))
        self.assertFalse(p.predict("1*+1"))
        self.assertFalse(p.predict("1+*1"))
        self.assertFalse(p.predict("1++1"))
        self.assertFalse(p.predict("+1*"))
        self.assertFalse(p.predict("+1*1"))

    def test_bbs(self):
        g = Grammar(['S'], list('()'), 'S')
        g.add_rule('S', '')
        g.add_rule('S', '(S)S')
        p = LR(g)
        self.assertTrue(p.predict(""))
        self.assertTrue(p.predict("()()"))
        self.assertTrue(p.predict("((()))"))
        self.assertTrue(p.predict("()(())(()(()()))"))
        self.assertFalse(p.predict(")"))
        self.assertFalse(p.predict("("))
        self.assertFalse(p.predict(")()("))
        self.assertFalse(p.predict("()(()((()))"))

    def test_bbs_large(self):
        g = Grammar(['S'], list('()'), 'S')
        g.add_rule('S', '')
        g.add_rule('S', '(S)S')
        p = LR(g)
        self.assertTrue(p.predict('()' * 10000))
        self.assertTrue(p.predict('(' * 10000 + ')' * 10000))
        self.assertTrue(p.predict('()(())' * 3000))
        self.assertFalse(p.predict('(' * 10000))
        self.assertFalse(p.predict(')' * 10000))
        self.assertFalse(p.predict('(' + '()' * 10000))
        self.assertFalse(p.predict('(' * 10000 + ')' * 10001))

    def test_not_lr(self):
        g = Grammar(list("SAB"), list("abcdz"), 'S')
        g.add_rule('S', 'aAc')
        g.add_rule('S', 'aBcd')
        g.add_rule('A', 'z')
        g.add_rule('B', 'z')
        self.assertRaises(ValueError, lambda: LR(g))
