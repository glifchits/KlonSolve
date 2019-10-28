from solver import *
import unittest


class TestSolver(unittest.TestCase):
    def test_build2suit_regex(self):
        self.assertIsNotNone(build2suit.match("2C"))
        self.assertIsNotNone(build2suit.match("1D"))
        self.assertIsNotNone(build2suit.match("7S"))
        self.assertIsNotNone(build2suit.match("3H"))
        self.assertIsNone(build2suit.match("D1"))
        self.assertIsNone(build2suit.match("1d"))
        self.assertIsNone(build2suit.match("9S"))
        self.assertIsNone(build2suit.match("1K"))
        self.assertIsNone(build2suit.match("x2C"))
        self.assertIsNone(build2suit.match("2Cx"))

    def test_talon2build_regex(self):
        self.assertIsNotNone(talon2build.match("W1"))
        self.assertIsNotNone(talon2build.match("W7"))
        self.assertIsNone(talon2build.match("W9"))
        self.assertIsNone(talon2build.match("W0"))
        self.assertIsNone(talon2build.match("w0"))
        self.assertIsNone(talon2build.match("15"))
        self.assertIsNone(talon2build.match("D5"))
        self.assertIsNone(talon2build.match("W7x"))
        self.assertIsNone(talon2build.match("xW7"))

    def test_suit2build_regex(self):
        self.assertIsNotNone(suit2build.match("C6"))
        self.assertIsNotNone(suit2build.match("D1"))
        self.assertIsNotNone(suit2build.match("S7"))
        self.assertIsNotNone(suit2build.match("H2"))
        self.assertIsNone(suit2build.match("13"))
        self.assertIsNone(suit2build.match("4D"))
        self.assertIsNone(suit2build.match("W1"))
        self.assertIsNone(suit2build.match("1W"))
        self.assertIsNone(suit2build.match("D1x"))
        self.assertIsNone(suit2build.match("xD1"))

    def test_drawmove_regex(self):
        self.assertIsNotNone(drawmove.match("DR1"))
        self.assertIsNotNone(drawmove.match("DR8"))
        self.assertIsNotNone(drawmove.match("DR10"))
        self.assertIsNotNone(drawmove.match("DR19"))
        self.assertIsNone(drawmove.match("DR0"))
        self.assertIsNone(drawmove.match("xDR1"))
        self.assertIsNone(drawmove.match("W1"))
        self.assertIsNone(drawmove.match("11"))


if __name__ == "__main__":
    unittest.main()
