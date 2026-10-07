import unittest
from clamp import clamp

class ClampTests(unittest.TestCase):
    def test_inside(self): self.assertEqual(clamp(4, 1, 7), 4)
    def test_below(self): self.assertEqual(clamp(-4, 1, 7), 1)
    def test_above(self): self.assertEqual(clamp(10, 1, 7), 7)
    def test_lower_boundary(self): self.assertEqual(clamp(1, 1, 7), 1)
    def test_upper_boundary(self): self.assertEqual(clamp(7, 1, 7), 7)
    def test_equal_bounds(self): self.assertEqual(clamp(100, 3, 3), 3)
    def test_float(self): self.assertAlmostEqual(clamp(2.5, 1.1, 3.3), 2.5)
    def test_negative_range(self): self.assertEqual(clamp(-4, -8, -2), -4)
    def test_reversed_bounds(self):
        with self.assertRaises(ValueError): clamp(4, 7, 1)

if __name__ == '__main__': unittest.main()
