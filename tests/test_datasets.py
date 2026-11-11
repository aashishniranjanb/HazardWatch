import unittest
import os
import sys

class TestDatasetIntegrity(unittest.TestCase):
    def test_multi_sensor_dataset(self):
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'multi_sensor_data.csv')
        self.assertTrue(os.path.exists(csv_path))
        with open(csv_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        self.assertEqual(len(lines), 813) # 1 header + 812 data rows

    def test_baseline_dataset(self):
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'multi_sensor_data_baseline.csv')
        self.assertTrue(os.path.exists(csv_path))
        with open(csv_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        self.assertEqual(len(lines), 12176) # 1 header + 12,175 rows

    def test_mq2_dataset(self):
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'mq2_data.csv')
        self.assertTrue(os.path.exists(csv_path))
        with open(csv_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        self.assertEqual(len(lines), 16041) # 1 header + 16,040 rows (including the 46 malformed rows)

if __name__ == '__main__':
    unittest.main()
