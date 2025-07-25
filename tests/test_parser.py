import unittest
from core.parser import parse_date, clean_amount

class TestParser(unittest.TestCase):
    def test_parse_date(self):
        self.assertIsNotNone(parse_date("01/15/2023"))
        self.assertIsNotNone(parse_date("Jan 15, 2023"))
        
    def test_clean_amount(self):
        self.assertEqual(clean_amount("$123.45"), 123.45)
        self.assertEqual(clean_amount("(123.45)"), -123.45)