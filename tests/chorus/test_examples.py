import unittest
import os

class TestExamples(unittest.TestCase):
    def test_example_importable(self):
        for example_path in os.listdir("examples/python/"):
            print(f"Testing example {example_path}")
            with open(f"examples/python/{example_path}") as f:
                exec(f.read(), {})
