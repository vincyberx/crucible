import hashlib
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wrap import wrap  # noqa: E402


def layout_cost(lines, width):
    """Cost of a layout exactly as the specification defines it."""
    total = 0
    for idx, line in enumerate(lines):
        words = line.split(" ")
        if idx == len(lines) - 1:
            continue
        if len(words) == 1 and len(line) > width:
            continue
        total += (width - len(line)) ** 2
    return total


def check_layout(tc, text, width, lines):
    tc.assertEqual(" ".join(lines).split(" "), text.split(), "words lost, reordered or re-spaced")
    for line in lines:
        tc.assertTrue(line and line == line.strip() and "  " not in line, repr(line))
        tc.assertTrue(len(line) <= width or " " not in line, "line too long: %r" % line)


def lcg_text(n, seed=12345):
    vocab = (
        "time person year way day thing man world life hand part child eye woman place work "
        "week case point government company number group problem fact be have do say get make "
        "go know take see come think look want give use find tell ask seem feel try leave call "
        "good new first last long great little own other old right big high different small "
        "large next early young important few public bad same able to of in for on with at by "
        "from up about into over after"
    ).split()
    x = seed
    out = []
    for _ in range(n):
        x = (x * 1103515245 + 12345) % 2147483648
        out.append(vocab[(x >> 16) % len(vocab)])
    return " ".join(out)


class TestOptimality(unittest.TestCase):
    def test_greedy_is_not_optimal(self):
        # greedy: "aaa bb" / "cc" / "ddddd" costs 0 + 16 = 16; optimum costs 9 + 1 = 10
        self.assertEqual(wrap("aaa bb cc ddddd", 6), ["aaa", "bb cc", "ddddd"])

    def test_greedy_is_not_optimal_2(self):
        out = wrap("xx yyy z ww vvv uu t", 5)
        self.assertEqual(layout_cost(out, 5), 18)
        self.assertEqual(out, ["xx", "yyy", "z ww", "vvv", "uu t"])

    def test_last_line_is_free(self):
        # 16 + 1 + 0 = 17; charging the last line would prefer "sea we" / "in which"
        self.assertEqual(wrap("way at sea we in which", 10), ["way at", "sea we in", "which"])

    def test_lorem_16(self):
        text = ("Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor "
                "incididunt ut labore et dolore magna aliqua")
        out = wrap(text, 16)
        check_layout(self, text, 16, out)
        self.assertEqual(layout_cost(out, 16), 128)
        self.assertEqual(out, ["Lorem ipsum", "dolor sit amet", "consectetur", "adipiscing",
                               "elit sed do", "eiusmod tempor", "incididunt ut",
                               "labore et dolore", "magna aliqua"])

    def test_long_word_in_the_middle(self):
        out = wrap("it was supercalifragilistic and fun", 8)
        self.assertEqual(out, ["it was", "supercalifragilistic", "and fun"])

    def test_long_paragraph_cost(self):
        text = lcg_text(600)
        for width, cost, nlines in ((30, 724, 108), (47, 537, 69), (72, 334, 45)):
            out = wrap(text, width)
            check_layout(self, text, width, out)
            self.assertEqual(layout_cost(out, width), cost, "width %d" % width)
            self.assertEqual(len(out), nlines, "width %d" % width)


class TestTies(unittest.TestCase):
    def test_tie_prefers_more_words_on_earlier_line(self):
        # "we"/"saw a"/"fox"/"go" and "we"/"saw"/"a fox"/"go" both cost 9 + 0 + 4 = 13;
        # the first lines are equal, the second line decides: "saw a" has more words.
        self.assertEqual(wrap("we saw a fox go", 5), ["we", "saw a", "fox", "go"])

    def test_tie_2(self):
        self.assertEqual(wrap("key be it in we small house", 9),
                         ["key be", "it in we", "small", "house"])

    def test_tie_3(self):
        self.assertEqual(wrap("sound old a box or be still", 6),
                         ["sound", "old a", "box", "or be", "still"])

    def test_tie_lorem_12(self):
        text = ("Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor "
                "incididunt ut labore et dolore magna aliqua")
        out = wrap(text, 12)
        self.assertEqual(layout_cost(out, 12), 131)
        self.assertEqual(out, ["Lorem ipsum", "dolor", "sit amet", "consectetur", "adipiscing",
                               "elit sed", "do eiusmod", "tempor", "incididunt", "ut labore et",
                               "dolore magna", "aliqua"])

    def test_tie_rule_on_long_paragraph(self):
        out = wrap(lcg_text(600), 47)
        digest = hashlib.sha256("\n".join(out).encode()).hexdigest()
        self.assertEqual(digest, "e053102ada95363b2cce3e09f0866566ef874c37815ad0d03ecb530f13eac592")


class TestValidation(unittest.TestCase):
    def test_width_must_be_positive(self):
        for bad in (0, -3):
            with self.assertRaises(ValueError):
                wrap("a b c", bad)


if __name__ == "__main__":
    unittest.main()
