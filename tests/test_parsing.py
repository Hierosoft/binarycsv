import os
import sys
import unittest

from collections import OrderedDict

if __name__ == '__main__':
    TESTS_DIR = os.path.dirname(os.path.realpath(__file__))
    REPO_DIR = os.path.dirname(TESTS_DIR)
    sys.path.insert(0, REPO_DIR)

from binarycsv import (
    pformat,
)


class Testing(unittest.TestCase):
    def test_pformat(self):
        self.assertEqual(pformat("abc"), '"abc"')
        self.assertEqual(pformat(1), '1')
        od = OrderedDict(
            a=2,
            b="c",
        )
        self.assertEqual(pformat(od), '{\'a\': 2, \'b\': "c", }')


if __name__ == '__main__':
    unittest.main()
