import unittest
from feature_checks import matching_records

class ComparisonTests(unittest.TestCase):
    def test_entity_alignment_not_row_order(self):
        matching_records([{"id":"b","x":2},{"id":"a","x":1}],
                         [{"id":"a","x":1},{"id":"b","x":2}],"id",["x"])
    def test_missing_entity_is_error(self):
        with self.assertRaises(RuntimeError):
            matching_records([], [{"id":"a","x":1}], "id", ["x"])
    def test_duplicate_entity_is_error(self):
        with self.assertRaises(RuntimeError):
            matching_records([{"id":"a","x":1}]*2,[{"id":"a","x":1}],"id",["x"])
    def test_future_value_is_error(self):
        with self.assertRaises(RuntimeError):
            matching_records([{"id":"a","x":1}],[{"id":"a","x":None}],"id",["x"])
    def test_nan_is_error(self):
        with self.assertRaises(RuntimeError):
            matching_records([{"id":"a","x":float("nan")}],[{"id":"a","x":1}],"id",["x"])
    def test_unavailable_feature_matches_null(self):
        matching_records([{"id":"a","x":None}],[{"id":"a","x":None}],"id",["x"])

if __name__=="__main__":
    unittest.main()
